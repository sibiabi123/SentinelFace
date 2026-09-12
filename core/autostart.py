import subprocess
import sys
import logging
from pathlib import Path

log = logging.getLogger(__name__)
TASK_NAME = "SentinelFace-Autostart"


def _pythonw_path() -> str:
    exe = Path(sys.executable)
    pythonw = exe.parent / "pythonw.exe"
    return str(pythonw) if pythonw.exists() else str(exe)


def register_autostart(main_py_path: str) -> bool:
    """Registers a per-user Scheduled Task that runs SentinelFace silently
    (pythonw, no console window) at logon, with LIMITED (non-admin) run
    level. Requires 'schtasks', which ships with Windows."""
    pythonw = _pythonw_path()
    cmd = [
        "schtasks", "/Create", "/TN", TASK_NAME,
        "/TR", f'"{pythonw}" "{main_py_path}"',
        "/SC", "ONLOGON", "/RL", "LIMITED", "/F",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log.info("Registered SentinelFace autostart task.")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to register autostart: {e.stderr}")
        return False


def remove_autostart() -> bool:
    cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log.info("Removed SentinelFace autostart task.")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to remove autostart: {e.stderr}")
        return False
