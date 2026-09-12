import os
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

def _startup_vbs_path() -> Path:
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "SentinelFace.vbs"

def register_autostart(main_py_path: str) -> bool:
    """Registers autostart silently via Task Scheduler or User Startup Folder fallback."""
    pythonw = _pythonw_path()
    
    # Method 1: Task Scheduler
    user = os.environ.get("USERNAME", "")
    cmd = [
        "schtasks", "/Create", "/TN", TASK_NAME,
        "/TR", f'"{pythonw}" "{main_py_path}"',
        "/SC", "ONLOGON", "/IT", "/F"
    ]
    if user:
        cmd.extend(["/RU", user])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            log.info("Registered SentinelFace autostart via Task Scheduler.")
            return True
    except Exception as e:
        log.warning(f"Task Scheduler registration attempt: {e}")

    # Method 2: User Startup Folder VBScript (100% reliable, zero admin privileges needed)
    try:
        vbs_file = _startup_vbs_path()
        vbs_file.parent.mkdir(parents=True, exist_ok=True)
        vbs_content = f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run """" & "{pythonw}" & """ """ & "{main_py_path}" & """", 0, False\n'
        vbs_file.write_text(vbs_content, encoding="utf-8")
        log.info(f"Registered SentinelFace autostart via Startup Folder: {vbs_file}")
        return True
    except Exception as e:
        log.error(f"Failed to write startup script: {e}")
        return False

def remove_autostart() -> bool:
    """Removes both Task Scheduler entry and User Startup Folder shortcut."""
    success = False
    
    # Remove Task Scheduler entry
    cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
    try:
        subprocess.run(cmd, capture_output=True, text=True)
        log.info("Removed Task Scheduler autostart entry.")
        success = True
    except Exception:
        pass

    # Remove Startup Folder VBScript
    try:
        vbs_file = _startup_vbs_path()
        if vbs_file.exists():
            vbs_file.unlink()
            log.info("Removed Startup Folder VBScript.")
            success = True
    except Exception as e:
        log.error(f"Failed to remove startup script: {e}")

    return success
