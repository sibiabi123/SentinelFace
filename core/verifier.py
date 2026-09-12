import json
import logging
from pathlib import Path

from camera.webcam import WebcamManager
from ai.detector import FaceDetector
from ai.recognizer import FaceRecognizer, RecognitionError
from ai.liveness import LivenessAnalyzer
from database.db import AuditDatabase
from core.locker import lock_windows_screen
from core.notifications import notify

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"


class VerificationEngine:
    """Orchestrates capture -> normalize -> recognize -> liveness -> log -> lock/continue.

    Two behavioral changes from the original that matter for security:
      1. A recognition backend failure (RecognitionError) is treated as a
         FAILED check, not skipped or passed. Fail closed, not open.
      2. The liveness score is now actually used to gate the PASS decision.
         Previously it was computed and logged but never checked.
    """

    def __init__(self, db: AuditDatabase = None):
        self.db = db or AuditDatabase()
        self.detector = FaceDetector()
        self.liveness = LivenessAnalyzer()
        self.load_config()

    def load_config(self):
        try:
            self.config = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
        except Exception:
            self.config = {}
        self.threshold = self.config.get("confidence_threshold", 0.60)
        self.verify_frames = self.config.get("verify_frames", 10)
        self.verify_required = self.config.get("verify_required", 6)
        self.min_agreement = self.config.get("min_agreement", 2)
        self.camera_index = self.config.get("camera_index", 0)
        self.auto_lock = self.config.get("auto_lock_enabled", True)
        self.liveness_required = self.config.get("liveness_required", True)
        self.recognizer = FaceRecognizer(threshold=self.threshold, min_agreement=self.min_agreement)
        self.webcam = WebcamManager(camera_index=self.camera_index)
        self.liveness.min_pass_score = self.config.get("liveness_min_score", 0.55)

    def _deny(self, result, notes, matches="0/0", confidence=0.0, liveness=0.0, is_manual_check=False):
        action = "LOCK_TRIGGERED" if (self.auto_lock and not is_manual_check) else "NONE"
        self.db.log_attempt(result=result, confidence=confidence, liveness=liveness,
                             matches=matches, action=action, notes=notes)
        if action == "LOCK_TRIGGERED":
            lock_windows_screen()
            notify("SentinelFace", "Face not verified — Windows locked.")
        return {"status": result, "message": notes, "confidence": confidence,
                "liveness": liveness, "matches": matches, "action": action}

    def run_verification(self, is_manual_check: bool = False) -> dict:
        self.load_config()

        if not self.recognizer.is_enrolled():
            msg = "No enrolled face profile found. Please enroll first."
            log.warning(msg)
            self.db.log_attempt("ERROR", 0.0, 0.0, "0/0", "NONE", msg)
            return {"status": "ERROR", "message": msg}

        frames = self.webcam.capture_frames(num_frames=self.verify_frames)
        if not frames:
            return self._deny("ABSENT", "Webcam unavailable or no frames captured.",
                               is_manual_check=is_manual_check)

        valid_frames = []
        matched_count = 0
        best_distances = []
        try:
            for frame in frames:
                norm = self.detector.normalize_lighting(frame)
                if self.detector.is_blurry(norm):
                    continue
                valid_frames.append(norm)
                embedding = self.recognizer.compute_embedding(norm)
                if embedding is None:
                    continue  # simply no face in this particular frame
                matched, dist, _ = self.recognizer.verify_embedding(embedding)
                best_distances.append(dist)
                if matched:
                    matched_count += 1
        except RecognitionError as e:
            # FAIL CLOSED. This is the fix for the original's most serious bug:
            # it used to fall back to "any detected face = match" here.
            log.error(f"Recognition backend failure - failing closed: {e}")
            return self._deny("ERROR", f"Recognition backend error, treated as failed verification: {e}",
                               is_manual_check=is_manual_check)

        if not valid_frames:
            return self._deny("ABSENT", "No usable (non-blurry) frames captured.",
                               is_manual_check=is_manual_check)

        liveness_result = self.liveness.evaluate(valid_frames)
        liveness_score = liveness_result["score"]
        avg_distance = sum(best_distances) / len(best_distances) if best_distances else 1.0
        confidence_pct = max(0.0, min(100.0, (1.0 - avg_distance) * 100.0))
        match_str = f"{matched_count}/{len(frames)}"

        identity_ok = matched_count >= self.verify_required
        liveness_ok = liveness_result["passed"] if self.liveness_required else True
        passed = identity_ok and liveness_ok

        if passed:
            self.db.log_attempt(result="PASS", confidence=confidence_pct, liveness=liveness_score,
                                 matches=match_str, action="CONTINUE",
                                 notes="Manual check" if is_manual_check else "Scheduled check")
            log.info(f"VERIFICATION PASSED: {match_str} matched, confidence={confidence_pct:.1f}%, liveness={liveness_score}")
            return {"status": "PASS", "confidence": confidence_pct, "liveness": liveness_score,
                    "matches": match_str, "action": "CONTINUE"}

        reasons = []
        if not identity_ok:
            reasons.append("face did not match enrolled profile")
        if not liveness_ok:
            reasons.append("liveness check failed (looked static/photo-like)")
        return self._deny("FAIL", "; ".join(reasons) or "verification failed", matches=match_str,
                           confidence=confidence_pct, liveness=liveness_score,
                           is_manual_check=is_manual_check)
