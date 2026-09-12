import cv2
import numpy as np
import logging

log = logging.getLogger(__name__)

_EYE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')


class LivenessAnalyzer:
    """
    Produces a basic liveness signal from a short burst of frames.

    Honesty note (read this before trusting it): this is a lightweight
    heuristic built from two weak signals — whole-frame motion, and
    eye-detection flicker across frames (a crude stand-in for blink
    detection). It raises the bar against someone holding up a single
    static printed photo. It is NOT a trained anti-spoofing model and
    will NOT reliably catch a video replay attack (e.g. playing a
    recording of you on a phone/tablet) or a photo moved slightly by
    hand. If you want real protection against that, you'd need a
    trained passive-anti-spoofing CNN or IR/depth hardware. Treat this
    as one extra speed bump, not a guarantee.
    """

    def __init__(self, motion_low: float = 0.3, motion_high: float = 25.0,
                 min_pass_score: float = 0.55):
        self.motion_low = motion_low
        self.motion_high = motion_high
        self.min_pass_score = min_pass_score

    def _motion_score(self, frames: list) -> float:
        if len(frames) < 2:
            return 0.0  # can't assess motion from a single frame - don't assume liveness
        diffs = []
        for i in range(len(frames) - 1):
            g1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            g2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
            diffs.append(float(np.mean(cv2.absdiff(g1, g2))))
        avg_motion = float(np.mean(diffs))
        if self.motion_low <= avg_motion <= self.motion_high:
            return min(1.0, 0.5 + avg_motion / 50.0)
        if avg_motion < self.motion_low:
            return 0.1   # suspiciously static -> looks like a still photo held in place
        return 0.3       # erratic/extreme motion -> also suspicious (camera being waved, etc.)

    def _blink_signal(self, frames: list) -> float:
        """A live face tends to show the eye-count flicker (2 -> 1/0 -> 2) of a
        blink somewhere across ~10 frames; a flat photo shows a constant count."""
        counts = []
        for f in frames:
            gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            eyes = _EYE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(20, 20))
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
