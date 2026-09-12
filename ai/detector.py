import cv2
import numpy as np
import logging

log = logging.getLogger(__name__)

class FaceDetector:
    """Preprocesses camera frames with CLAHE contrast enhancement and detects faces using OpenCV cascade/YuNet."""

    def __init__(self):
        self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def normalize_lighting(self, frame: np.ndarray) -> np.ndarray:
        """Applies CLAHE histogram equalization on YUV color space to normalize lighting."""
        if frame is None or frame.size == 0:
            return frame
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        yuv[:, :, 0] = self.clahe.apply(yuv[:, :, 0])
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

    def is_blurry(self, frame: np.ndarray, threshold: float = 30.0) -> bool:
        """Calculates Laplacian variance to detect blurry frames."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        return score < threshold

    def detect_faces(self, frame: np.ndarray) -> list:
        """Detects bounding boxes [(x, y, w, h)] for all faces in frame."""
        if frame is None:
            return []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        return list(faces)

    def has_face(self, frame: np.ndarray) -> bool:
        return len(self.detect_faces(frame)) > 0
