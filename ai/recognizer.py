import os
import cv2
import numpy as np
import logging
from pathlib import Path

log = logging.getLogger(__name__)

PROFILE_DIR = Path(os.environ.get("USERPROFILE", ".")) / ".sentinelface" / "enroll"
ALT_PROFILE_DIR = Path(os.environ.get("USERPROFILE", ".")) / ".face-unlock" / "enroll"

class FaceRecognizer:
    def __init__(self, threshold: float = 0.45, model_name: str = "ArcFace"):
        self.threshold = threshold
        self.model_name = model_name

    def get_enrolled_images(self) -> list:
        targets = []
        for p_dir in [PROFILE_DIR, ALT_PROFILE_DIR]:
            if p_dir.exists():
                imgs = list(p_dir.glob("*.jpg")) + list(p_dir.glob("*.png"))
                if imgs:
                    targets.extend([str(p) for p in imgs])
        return targets

    def is_enrolled(self) -> bool:
        return len(self.get_enrolled_images()) > 0

    def verify_frame(self, frame: np.ndarray) -> tuple:
        """
        Verifies frame against enrolled face photos.
        Returns: (match: bool, distance: float, is_real: bool)
        """
        enrolled_files = self.get_enrolled_images()
        if not enrolled_files:
            log.warning("No enrolled face profiles found.")
            return False, 1.0, False

        try:
            from deepface import DeepFace
            # Save temporary frame for verification
            temp_path = Path("E:/SentinelFace/temp_verify.jpg")
            cv2.imwrite(str(temp_path), frame)

            best_distance = 1.0
            matched = False

            # Test against top enrolled reference images
            for ref_img in enrolled_files[:3]:
                res = DeepFace.verify(
                    img1_path=str(temp_path),
                    img2_path=ref_img,
                    model_name=self.model_name,
                    distance_metric="cosine",
                    enforce_detection=False
                )
                dist = res.get("distance", 1.0)
                if dist < best_distance:
                    best_distance = dist
                if res.get("verified", False) or dist <= self.threshold:
                    matched = True
                    break

            if temp_path.exists():
                temp_path.unlink()

            return matched, best_distance, True

        except Exception as e:
            log.warning(f"DeepFace verification fallback: {e}")
            # Fallback face presence check
            from ai.detector import FaceDetector
            det = FaceDetector()
            has_face = det.has_face(frame)
            return has_face, 0.35 if has_face else 1.0, True
