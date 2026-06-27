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
    if executable.lower().endswith(("python.exe", "pythonw.exe")):
        params = " ".join([f'"{arg}"' for arg in sys.argv])
    else:
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    res = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
    return res > 32