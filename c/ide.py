from datetime import datetime
import ctypes
import sys
from PyQt5.QtWidgets import *
from built import *
_version_ = 1.0
lsit = [
  f"Running on {sys.platform.title()}",
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
                
            app = QApplication(sys.argv)
            
            window = QMainWindow()
            main_ui = MainUI(1920, 1080)
            window.setCentralWidget(main_ui)
            window.setWindowTitle("CArt")
            
            main_ui.console.write("=======DONT WRITE TO THIS CONSOLE!========", "system")
            
            window.show()
            sys.exit(app.exec_())
        
        except Exception as e:
            print("\n" + "="*50)
            print("🚨 CRITICAL STARTUP ERROR DETECTED:")
            print("="*50)
            import traceback
            traceback.print_exc()
            print("="*50)
            input("\nPress ENTER to close this window...")
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "ide.py", os.getcwd(), 1)