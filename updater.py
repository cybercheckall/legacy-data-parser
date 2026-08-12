import os
import sys
import tempfile
import subprocess
import requests
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

GITHUB_LATEST_JSON_URL = "https://github.com/cybercheckall/legacy-data-parser/releases/latest/download/latest.json"

def _parse_version(version_str):
    """Converts a version string like 'v1.0.0' to a tuple (1, 0, 0)."""
    return tuple(map(int, version_str.lower().strip("v").split(".")))

class BackgroundUpdater(QThread):
    """
    Silently checks for updates in the background.
    If an update is found, it downloads it and emits update_ready with the bat script path.
    """
    update_ready = pyqtSignal(str)
    
    def __init__(self, current_version, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        
    def run(self):
        try:
            logger.info("BackgroundUpdater: Checking for updates...")
            response = requests.get(GITHUB_LATEST_JSON_URL, timeout=10)
            if response.status_code != 200:
                logger.info("BackgroundUpdater: Failed to fetch latest release json.")
                return
                
            data = response.json()
            latest_version = data.get("version", "v0.0.0")
            download_url = data.get("url")
            
            if not download_url:
                return
                
            if _parse_version(latest_version) > _parse_version(self.current_version):
                logger.info(f"BackgroundUpdater: Found new version {latest_version}. Downloading silently...")
                
                temp_dir = tempfile.gettempdir()
                download_path = os.path.join(temp_dir, "Owl_update.exe")
                
                # Download file
                resp = requests.get(download_url, stream=True, timeout=20)
                resp.raise_for_status()
                
                with open(download_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                # Generate bat script
                current_exe = sys.executable
                bat_script_path = os.path.join(temp_dir, "update_owl.bat")
                
                bat_contents = f"""@echo off
echo Updating Owl Browser... Please wait.
:loop
timeout /t 1 /nobreak > NUL
copy /y "{download_path}" "{current_exe}" > NUL
if %ERRORLEVEL% neq 0 goto loop
del "{download_path}"
start "" "{current_exe}"
del "%~f0"
"""
                with open(bat_script_path, "w") as f:
                    f.write(bat_contents)
                    
                logger.info("BackgroundUpdater: Update downloaded and script prepared. Emitting update_ready.")
                self.update_ready.emit(bat_script_path)
                
        except Exception as e:
            logger.error(f"BackgroundUpdater: Error during background update: {e}")

def apply_update(bat_script_path):
    """Executes the bat script and exits the application."""
    logger.info("Applying update: spawning bat script and exiting.")
    try:
        subprocess.Popen(
            [bat_script_path], 
            creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    except Exception as e:
        logger.error(f"Failed to launch update script: {e}")
    finally:
        sys.exit(0)
