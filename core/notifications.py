import logging

log = logging.getLogger(__name__)

class ToastNotifier:
    """Delivers native Windows Toast Notifications for SentinelFace events."""

    @staticmethod
    def notify_pass(confidence: float, matches_str: str):
        try:
            from winotify import Notification, audio
            toast = Notification(
                app_id="SentinelFace",
                title="🛡️ SentinelFace: User Verified",
                msg=f"Identity confirmed ({confidence:.1f}% match, {matches_str} frames). Continuing session...",
                duration="short"
            )
            toast.show()
        except Exception as e:
            log.debug(f"Toast notification skipped: {e}")

    @staticmethod
    def notify_lock(reason: str = "User Absent / Unrecognized"):
        try:
            from winotify import Notification, audio
            toast = Notification(
                app_id="SentinelFace",
                title="🔒 SentinelFace: Locking PC",
                msg=f"Security alert: {reason}. Windows screen locked.",
                duration="short"
            )
            toast.set_audio(audio.Hand, loop=False)
            toast.show()
        except Exception as e:
            log.debug(f"Toast notification skipped: {e}")
