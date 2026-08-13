from built import *
from built import _version_
import sys as s
import os
from datetime import datetime
import ctypes
from PyQt5.QtWidgets import QApplication, QMainWindow

lsit = [
  f"Running on {s.platform.title()}",
  f"Version: {_version_}",
  f"os: Windows",
  f"dev: True",
  f"Time: {datetime.now()}"
]

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin():
        try:
            sp.run("taskkill /f /im noname.exe", shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
            
            for i in lsit:
                print(i)
                
            app = QApplication(s.argv)
            
            window = QMainWindow()
            main_ui = MainUI(1920, 1080)
            window.setCentralWidget(main_ui)
            window.setWindowTitle("C++Art")
            
            main_ui.console.write("=======DONT WRITE TO THIS CONSOLE!========", "system")
            
            window.show()
            s.exit(app.exec_())
        
        except Exception as e:
            print("\n" + "="*50)
            print("🚨 CRITICAL STARTUP ERROR DETECTED:")
            print("="*50)
            import traceback
            traceback.print_exc()
            print("="*50)
            input("\nPress ENTER to close this window...")
    else:
        # Ensures the elevated workspace stays fixed on your current working directory
        ctypes.windll.shell32.ShellExecuteW(None, "runas", s.executable, "ide.py", os.getcwd(), 1)