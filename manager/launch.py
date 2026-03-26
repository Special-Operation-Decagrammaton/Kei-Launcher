import os
import platform
import subprocess
import tkinter as tk
import webbrowser

from lib.helper import resource_path
from manager.interface import AppInterface

class LaunchManager:
    def __init__(self, app: AppInterface):
        self.app = app
        
    def setup_window(self):
        self.app.title("BA TL Launcher")
        self.center_window(960, 640)
        self.app.resizable(False, False)
        self.app._set_appearance_mode("dark")
        
    def center_window(self, width: int, height: int):
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.app.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_icon(self):
        try:
            system_os = platform.system()
            icon_name = "asset/kei.ico" if system_os == "Windows" else "asset/kei.png"
            icon_path = resource_path(icon_name)
            if os.path.exists(icon_path):
                if system_os == "Windows":
                    self.app.iconbitmap(icon_path)
                else:
                    img = tk.PhotoImage(file=icon_path)
                    self.app.wm_iconphoto(True, img)
        except Exception as e:
            print(f"Could not load window icon: {e}")
            
    def open_github_link(self):
        webbrowser.open("https://github.com/Special-Operation-Decagrammaton/BA-TL-Launcher")
            
    def launch_game(self):
        if not self.app.game_config.GamePath or not self.app.game_config.GamePath.exists():
            self.app.update_manager.display_status(text="Please set Game Folder first!", text_color="orange")
            self.app.btn_launch.configure(state="disabled")
            return
        
        bat_path = self.app.game_config.GamePath / "run.bat"
        if os.path.exists(bat_path):
            subprocess.Popen(["cmd", "/c", bat_path], cwd=self.app.game_config.GamePath, shell=True)
            self.app.quit()
        else:
            self.app.update_manager.display_status(text="BlueArchive.exe and run.bat not found!", text_color="red")

