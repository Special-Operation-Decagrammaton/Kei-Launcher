import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def run_admin():
    executable = sys.executable
    if executable.endswith("python.exe"):
        pw = executable.replace("python.exe", "pythonw.exe")
        if os.path.exists(pw):
            executable = pw
    res = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, " ".join(sys.argv), None, 1)
    return res > 32