import sys
import subprocess
import logging
from pathlib import Path

log = logging.getLogger(__name__)

TASK_NAME = "SentinelFace-Autostart"

class AutostartManager:
    """Registers or unregisters Windows Task Scheduler autostart for invisible background monitoring."""

    @staticmethod
    def is_registered() -> bool:
        cmd = f'schtasks /query /tn "{TASK_NAME}"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.returncode == 0

    @staticmethod
    def register_autostart() -> bool:
        pythonw_exe = Path(sys.executable).parent / "pythonw.exe"
        if not pythonw_exe.exists():
            pythonw_exe = Path(sys.executable)

        main_script = Path("E:/SentinelFace/main.py").resolve()
        
        # schtasks command running pythonw silently at user logon
        cmd = f'schtasks /create /tn "{TASK_NAME}" /tr "\"{pythonw_exe}\" \"{main_script}\" --tray" /sc onlogon /rl limited /f'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            log.info(f"Registered Task Scheduler autostart: {TASK_NAME}")
            return True
        else:
            log.error(f"Failed to register autostart: {res.stderr}")
            return False

    @staticmethod
    def unregister_autostart() -> bool:
        cmd = f'schtasks /delete /tn "{TASK_NAME}" /f'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            log.info(f"Unregistered Task Scheduler autostart: {TASK_NAME}")
            return True
        else:
            log.error(f"Failed to unregister autostart: {res.stderr}")
            return False
