import json
import logging
from pathlib import Path
from camera.webcam import WebcamManager
from ai.detector import FaceDetector
from ai.recognizer import FaceRecognizer
from ai.liveness import LivenessAnalyzer
from database.db import AuditDatabase
from core.locker import lock_windows_screen
from core.notifications import ToastNotifier

log = logging.getLogger(__name__)
CONFIG_PATH = Path("E:/SentinelFace/config.json")

class VerificationEngine:
    """Orchestrates multi-frame capture, lighting normalization, face verification, database logging, toast alerts, and locking."""

    def __init__(self, db: AuditDatabase = None):
        self.db = db or AuditDatabase()
        self.detector = FaceDetector()
        self.liveness = LivenessAnalyzer()
        self.load_config()

    def load_config(self):
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}

        self.threshold = self.config.get("confidence_threshold", 0.45)
        self.verify_frames = self.config.get("verify_frames", 10)
        self.verify_required = self.config.get("verify_required", 6)
        self.camera_index = self.config.get("camera_index", 0)
        self.auto_lock = self.config.get("auto_lock_enabled", True)
        self.show_toasts = self.config.get("show_toast_notifications", True)

        self.recognizer = FaceRecognizer(threshold=self.threshold)
        self.webcam = WebcamManager(camera_index=self.camera_index)

    def run_verification(self, is_manual_check: bool = False) -> dict:
        self.load_config()
        log.info(f"--- Running SentinelFace Verification Probe (Target: {self.verify_required}/{self.verify_frames} matches) ---")

        if not self.recognizer.is_enrolled():
            msg = "No enrolled face profile found. Please enroll face first!"
            log.warning(msg)
            self.db.log_attempt("ERROR", 0.0, 0.0, "0/0", "NONE", msg)
            return {"status": "ERROR", "message": msg}

        frames = self.webcam.capture_frames(num_frames=self.verify_frames)
        if not frames:
            msg = "Webcam unavailable or blocked by another application."
            log.error(msg)
            self.db.log_attempt("ABSENT", 1.0, 0.0, f"0/{self.verify_frames}", "LOCK_TRIGGERED" if self.auto_lock else "NONE", msg)
            if self.show_toasts and not is_manual_check:
                ToastNotifier.notify_lock("Webcam Unavailable / Blocked")
            if self.auto_lock and not is_manual_check:
                lock_windows_screen()
            return {"status": "ABSENT", "message": msg}

        # Multi-frame majority voting pipeline
        matched_count = 0
        distances = []
        valid_frames = []

        for frame in frames:
            norm_frame = self.detector.normalize_lighting(frame)
            if self.detector.is_blurry(norm_frame):
                continue
            valid_frames.append(norm_frame)

            matched, dist, _ = self.recognizer.verify_frame(norm_frame)
            distances.append(dist)
            if matched:
                matched_count += 1

        avg_distance = sum(distances) / len(distances) if distances else 1.0
        confidence_pct = max(0.0, min(100.0, (1.0 - avg_distance) * 100.0))
        liveness_score = self.liveness.evaluate_liveness(valid_frames if valid_frames else frames)

        match_str = f"{matched_count}/{len(frames)}"
        passed = matched_count >= self.verify_required

        if passed:
            result = "PASS"
            action = "CONTINUE"
            log.info(f"VERIFICATION SUCCESSFUL: Matched {match_str} frames (Confidence: {confidence_pct:.1f}%). User verified!")
            if self.show_toasts and not is_manual_check:
                ToastNotifier.notify_pass(confidence_pct, match_str)
        else:
            result = "FAIL" if len(valid_frames) > 0 else "ABSENT"
            action = "LOCK_TRIGGERED" if (self.auto_lock and not is_manual_check) else "NONE"
            log.warning(f"VERIFICATION FAILED: Matched {match_str} frames. Action: {action}")
            if self.show_toasts and not is_manual_check:
                ToastNotifier.notify_lock(f"Unrecognized Face / User Absent ({match_str} matches)")

        self.db.log_attempt(
            result=result,
            confidence=confidence_pct,
            liveness=liveness_score,
            matches=match_str,
            action=action,
            notes="Manual check" if is_manual_check else "Scheduled check"
        )

        if passed:
            return {
                "status": "PASS",
                "confidence": confidence_pct,
                "liveness": liveness_score,
                "matches": match_str,
                "action": action
            }
        else:
            if self.auto_lock and not is_manual_check:
                lock_windows_screen()
            return {
                "status": result,
                "confidence": confidence_pct,
                "liveness": liveness_score,
                "matches": match_str,
                "action": action
            }
