from datetime import datetime
import os
import sys
import platform
import subprocess as sp
from PyQt5.QtWidgets import QApplication, QMainWindow
from built import MainUI, _version_

list_info = [
    f"Running on: {sys.platform}",
    f"OS Family: {platform.system()}",
    f"Version: {_version_}",
    f"Dev Mode: True",
    f"Time: {datetime.now()}"
]

def kill_previous_instances():
    """Cross-platform binary process termination."""
    try:
        if sys.platform == "win32":
            sp.run("taskkill /f /im noname.exe", shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        else:
            sp.run(["pkill", "-f", "noname"], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    except Exception:
        pass

if __name__ == "__main__":
    kill_previous_instances()

    for item in list_info:
        print(item)

    try:
        app = QApplication(sys.argv)
        
        window = QMainWindow()
        main_ui = MainUI(1280, 720)
        window.setCentralWidget(main_ui)
        window.setWindowTitle(f"CArt IDE - ({platform.system()})")
        
        main_ui.console.write("======= CROSS-PLATFORM C IDE STARTED =======\n", "system")
        
        window.show()
        sys.exit(app.exec_())
    
    except Exception as e:
        print("\n" + "="*50)
        print("🚨 CRITICAL STARTUP ERROR DETECTED:")
        print("="*50)
        import traceback
        traceback.print_exc()
        print("="*50)
        if sys.platform == "win32":
            input("\nPress ENTER to close this window...")
