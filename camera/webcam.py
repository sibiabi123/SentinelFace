import cv2
import time
import logging

log = logging.getLogger(__name__)

class WebcamManager:
    """On-demand webcam driver that opens the camera sensor briefly and releases hardware immediately."""

    def __init__(self, camera_index: int = 0, warmup_frames: int = 5):
        self.camera_index = camera_index
        self.warmup_frames = warmup_frames

    def capture_frames(self, num_frames: int = 10) -> list:
        """Opens camera, reads auto-exposure warmup frames, captures num_frames, and closes camera."""
        frames = []
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            log.error(f"Failed to open camera index {self.camera_index}")
            return frames

        try:
            # Allow camera sensor & auto-exposure to warm up
            time.sleep(0.5)
            for _ in range(self.warmup_frames):
                cap.read()

            for _ in range(num_frames):
                ret, frame = cap.read()
                if ret and frame is not None:
                    frames.append(frame)
                time.sleep(0.05)
        finally:
            cap.release()
            log.info(f"Captured {len(frames)} frames and released webcam hardware (LED OFF).")

        return frames
