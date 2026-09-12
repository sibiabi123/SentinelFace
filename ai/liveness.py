import cv2
import numpy as np
import logging

log = logging.getLogger(__name__)

def _get_eye_cascade():
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        if hasattr(cv2, 'CascadeClassifier'):
            return cv2.CascadeClassifier(cascade_path)
        else:
            return getattr(cv2, 'CascadeClassifier')(cascade_path)
    except Exception as e:
        log.error(f"Failed to load eye cascade: {e}")
        return None

class LivenessAnalyzer:
    """
    Produces a basic liveness signal from a short burst of frames.
    Evaluates whole-frame motion and eye-detection flicker.
    """

    def __init__(self, motion_low: float = 0.3, motion_high: float = 25.0,
                 min_pass_score: float = 0.55):
        self.motion_low = motion_low
        self.motion_high = motion_high
        self.min_pass_score = min_pass_score
        self._eye_cascade = None

    def _get_cascade(self):
        if self._eye_cascade is None:
            self._eye_cascade = _get_eye_cascade()
        return self._eye_cascade

    def _motion_score(self, frames: list) -> float:
        if len(frames) < 2:
            return 0.0
        diffs = []
        for i in range(len(frames) - 1):
            g1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            g2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
            diffs.append(float(np.mean(cv2.absdiff(g1, g2))))
        avg_motion = float(np.mean(diffs))
        if self.motion_low <= avg_motion <= self.motion_high:
            return min(1.0, 0.5 + avg_motion / 50.0)
        if avg_motion < self.motion_low:
            return 0.1
        return 0.3

    def _blink_signal(self, frames: list) -> float:
        cascade = self._get_cascade()
        if cascade is None:
            return 0.5  # Neutral fallback if eye cascade unavailable

        counts = []
        for f in frames:
            gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            eyes = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(20, 20))
            counts.append(len(eyes))
        if len(counts) < 2:
            return 0.0
        variation = float(np.std(counts))
        return min(1.0, variation / 1.5)

    def evaluate(self, frames: list) -> dict:
        motion = self._motion_score(frames)
        blink = self._blink_signal(frames)
        score = round(0.6 * motion + 0.4 * blink, 2)
        return {
            "score": score,
            "motion_component": round(motion, 2),
            "blink_component": round(blink, 2),
            "passed": score >= self.min_pass_score,
        }
