import logging

log = logging.getLogger(__name__)

_icon_ref = {"icon": None}


def set_tray_icon(icon):
    """Called once by tray.py after the pystray icon is created, so notify()
    can use its native balloon/toast on Windows."""
    _icon_ref["icon"] = icon


def notify(title: str, message: str):
    """Best-effort desktop notification. Uses the tray icon's native balloon
    (pystray -> Windows Shell notification) if the tray app is running;
    otherwise just logs. This is intentionally modest - a previous version
    of this project claimed a fully native toast pipeline that was never
    actually wired up in the code."""
    icon = _icon_ref.get("icon")
    if icon is not None:
        try:
            icon.notify(message, title)
            return
        except Exception as e:
            log.debug(f"Tray notification failed, falling back to log only: {e}")
    log.info(f"[NOTIFY] {title}: {message}")
