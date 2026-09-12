import ctypes
import logging

log = logging.getLogger(__name__)


def lock_windows_screen() -> bool:
    """Triggers the standard Windows lock screen (equivalent to Win+L)."""
    log.warning("SentinelFace: triggering LockWorkStation()...")
    try:
        ctypes.windll.user32.LockWorkStation()
        return True
    except Exception as e:
        log.error(f"Failed to trigger LockWorkStation: {e}")
        return False
