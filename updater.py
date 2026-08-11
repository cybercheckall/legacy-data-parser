import os
import sys
import tempfile
import subprocess
import requests
from PyQt6.QtWidgets import QMessageBox, QProgressDialog
from PyQt6.QtCore import Qt

GITHUB_LATEST_JSON_URL = "https://github.com/Raghuvaranlokati/private-brower/releases/latest/download/latest.json"

def _parse_version(version_str):
    """Converts a version string like 'v1.0.0' to a tuple (1, 0, 0)."""
    return tuple(map(int, version_str.lower().strip("v").split(".")))

def check_for_updates(current_version, parent_widget=None):
    """
    Checks GitHub for a new version.
    Returns True if an update was found and applied (meaning the app should exit),
    otherwise returns False.
    """
    try:
        response = requests.get(GITHUB_LATEST_JSON_URL, timeout=5)
        if response.status_code != 200:
            return False
            
        data = response.json()
        latest_version = data.get("version", "v0.0.0")
        download_url = data.get("url")
        
        if not download_url:
            return False
            
        if _parse_version(latest_version) > _parse_version(current_version):
            # Update available!
            reply = QMessageBox.question(
                parent_widget,
                "Update Available",
                f"A new version of the browser ({latest_version}) is available.\n\nWould you like to install it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                _download_and_apply_update(download_url, parent_widget)
                return True
                
    except Exception as e:
        print(f"Failed to check for updates: {e}")
        
    return False

def _download_and_apply_update(download_url, parent_widget):
    """Downloads the new exe and runs the replacement batch script."""
    temp_dir = tempfile.gettempdir()
    download_path = os.path.join(temp_dir, "Owl_update.exe")
    
    try:
        response = requests.get(download_url, stream=True, timeout=10)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        
        # Setup Progress Dialog
        progress = QProgressDialog("Downloading update...", "Cancel", 0, total_size, parent_widget)
        progress.setWindowTitle("Updating")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        downloaded_size = 0
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if progress.wasCanceled():
                    if os.path.exists(download_path):
                        os.remove(download_path)
                    return
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    progress.setValue(downloaded_size)
                    
        progress.setValue(total_size)
        
        # Now generate the replacement bat script
        current_exe = sys.executable
        bat_script_path = os.path.join(temp_dir, "update_owl.bat")
        
        bat_contents = f"""@echo off
echo Updating Owl Browser... Please wait.
timeout /t 2 /nobreak > NUL
copy /y "{download_path}" "{current_exe}"
del "{download_path}"
start "" "{current_exe}"
del "%~f0"
"""
        with open(bat_script_path, "w") as f:
            f.write(bat_contents)
            
        # Launch the bat script completely detached and exit the current app
        subprocess.Popen(
            [bat_script_path], 
            creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        sys.exit(0)
        
    except Exception as e:
        QMessageBox.critical(parent_widget, "Update Failed", f"Failed to download the update:\n{str(e)}")
        if os.path.exists(download_path):
            os.remove(download_path)
