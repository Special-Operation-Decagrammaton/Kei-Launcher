import os
import platform
import subprocess
import webbrowser
import customtkinter as ctk

from config import VERSION

from lib.helper import resource_path
from manager.interface import AppInterface

class LaunchManager:
    def __init__(self, app: AppInterface):
        self.app = app
        
    def setup_window(self):
        self.app.title("BA TL Launcher")
        self.center_window(960, 640)
        self.app.resizable(False, False)
        
    def center_window(self, width: int, height: int):
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.app.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_icon(self, window=None):
        import tkinter as tk
        if window is None:
            window = self.app
        try:
            system_os = platform.system()
            icon_name = "asset/kei.ico" if system_os == "Windows" else "asset/kei.png"
            icon_path = resource_path(icon_name)
            if os.path.exists(icon_path):
                if system_os == "Windows":
                    window.after(200, lambda: window.iconbitmap(icon_path))
                else:
                    img = tk.PhotoImage(file=icon_path)
                    window.wm_iconphoto(True, img)
        except Exception as e:
            print(f"Could not load window icon: {e}")
            
    def open_github_link(self):
        webbrowser.open("https://github.com/Special-Operation-Decagrammaton/Kei-Launcher")
            
    def launch_game(self):
        if not self.app.game_config.GamePath or not self.app.game_config.GamePath.exists():
            self.app.update_manager.display_status(text="Please set Game Folder first!", text_color="orange")
            self.app.btn_launch.configure(state="disabled")
            return
        
        bat_path = self.app.game_config.GamePath / "run.bat"
        if os.path.exists(bat_path):
            try:
                cmd = f"Start-Process '{bat_path}' -Verb RunAs -WorkingDirectory '{self.app.game_config.GamePath}'"
                subprocess.run(["powershell", "-Command", cmd], check=True, capture_output=True, text=True)
                
                if self.app.game_config.CloseOnLaunch:
                    self.app.quit()
            except subprocess.CalledProcessError as e:
                if "canceled by the user" in e.stderr or e.returncode != 0:
                    self.app.update_manager.display_status(text="Launch cancelled (UAC).", text_color="orange")
                else:
                    self.app.update_manager.display_status(text="Launch error.", text_color="red")
        else:
            self.app.update_manager.display_status(text="BlueArchive.exe and run.bat not found!", text_color="red")
            
    def show_settings_popup(self):
        if hasattr(self, 'settings_popup') and self.settings_popup.winfo_exists():
            self.settings_popup.focus()
            return
            
        popup = ctk.CTkToplevel(self.app)
        self.settings_popup = popup
        popup.title("Settings")
        
        width, height = 400, 300
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.resizable(False, False)
        popup.transient(self.app)
        self.setup_icon(popup)

        title_label = ctk.CTkLabel(popup, text="Kei Launcher", font=("Roboto", 18, "bold"))
        title_label.pack(pady=(15, 5))

        version_label = ctk.CTkLabel(popup, text=f"Version: v{VERSION}", font=("Roboto", 14))
        version_label.pack(pady=5)
        
        def toggle_col():
            self.app.setting_manager.toggle_close_on_launch(close_on_launch_var.get())

        close_on_launch_var = ctk.BooleanVar(value=self.app.game_config.CloseOnLaunch)
        col_switch = ctk.CTkSwitch(
            popup, text="Close Launcher on Game Launch", 
            variable=close_on_launch_var, 
            command=toggle_col,
            font=("Roboto", 14)
        )
        col_switch.pack(pady=15)
        

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5, 0), padx=20)

        github_btn = ctk.CTkButton(
            btn_frame, text="GitHub Repository", 
            command=self.open_github_link,
            width=120
        )
        github_btn.pack(side="left", expand=True, padx=5)

        update_btn = ctk.CTkButton(
            btn_frame, text="Check Update",
            command=lambda: self.app.update_manager.start_check_launcher_update_thread(on_status=update_status),
            width=120
        )
        update_btn.pack(side="right", expand=True, padx=5)

        status_label = ctk.CTkLabel(popup, text="", font=("Roboto", 12))
        status_label.pack(pady=10)

        def update_status(msg, color):
            status_label.configure(text=msg, text_color=color)