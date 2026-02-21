from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import platform

import customtkinter as ctk
import tkinter as tk
import requests
import os
import threading
import subprocess

from tkinter import filedialog
from lib.checker import check_game_executable, check_new_update
from lib.helper import resource_path
from lib.permission import is_admin, run_admin
from config import (
    REPO,
    CONFIG_DIR,
    CONFIG_PATH,
    MANIFEST_PATH
)
from model.manifest import (
    GameFileInfo,
    load_manifest,
    load_manifest_memory,
    save_manifest
)
from model.config import (
    Branch,
    LauncherConfig,
    Language,
    BuildTag,
    load_config,
    save_config
)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BA TL Launcher")
        self.geometry("640x480")
        self.resizable(False, False)
        try:
            icon_name = "kei.ico" if platform.system() == "Windows" else "kei.png"
            icon_path = resource_path(icon_name)
            if os.path.exists(icon_path):
                if platform.system() == "Windows":
                    self.iconbitmap(icon_path)
                else:
                    img = tk.PhotoImage(file=icon_path)
                    self.wm_iconphoto(True, img)
        except Exception as e:
            print(f"Could not load window icon: {e}")
        
        self.game_config = LauncherConfig(
            GamePath="",
            Language=Language.EN.value,
            Branch=Branch.MAIN.value,
            BuildTag=BuildTag.LATEST.value,
            CloseOnLaunch=True
        )
        self.game_manifest = None
        self.load_launcher_config()

        # UI Layout
        self.label = ctk.CTkLabel(self, text="BA TL Launcher", font=("Roboto", 24, "bold"))
        self.label.pack(pady=30)

        self.progress_bar = ctk.CTkProgressBar(self, width=600)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()
        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack(side="bottom")

        # Button Container (Bottom)
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(side="bottom", fill="x", padx=20, pady=10)

        # Left Buttons
        self.btn_check = ctk.CTkButton(self.button_frame, text="Check for Updates", command=self.check_updates)
        self.btn_check.pack(side="left", padx=5)

        self.btn_folder = ctk.CTkButton(self.button_frame, text="Set Game Folder", command=self.set_game_folder)
        self.btn_folder.pack(side="left", padx=5)

        # Right Buttons
        self.btn_launch = ctk.CTkButton(self.button_frame, text="Launch", fg_color="green", hover_color="darkgreen", command=self.launch_game)
        self.btn_launch.pack(side="right", padx=5)

        self.btn_update = ctk.CTkButton(self.button_frame, text="Update TL", command=self.start_update_thread)
        self.btn_update.pack(side="right", padx=5)

        if not self.game_config.GamePath:
            self.status_label.configure(text="Please set Game Folder first!", text_color="orange")

    def load_launcher_config(self):
        if os.path.exists(CONFIG_PATH):
            self.game_config = load_config(CONFIG_PATH)
        if os.path.exists(MANIFEST_PATH):
            self.game_manifest = load_manifest(MANIFEST_PATH)
        
    def set_game_folder(self):
        folder = Path(filedialog.askdirectory(title="Select BlueArchive_JP Folder"))
        if folder:
            if check_game_executable(folder):
                if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
                self.game_config.GamePath = folder
                save_config(self.game_config, CONFIG_PATH)
                self.status_label.configure(text=f"Path set: {folder}", text_color="green")
            else:
                self.status_label.configure(text="Error: BlueArchive.exe and run.bat not found!", text_color="red")

    def check_updates(self):
        self.status_label.configure(text="Checking manifest...", text_color="yellow")
        url = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{self.game_config.Branch.value}/GameManifest.json"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                latest_manifest = load_manifest_memory(response.content)
                textMsg, textColor = check_new_update(self.game_config, self.game_manifest, latest_manifest)
                self.status_label.configure(text=textMsg, text_color=textColor)
            else:
                self.status_label.configure(text="No updates found.", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"API Error: {str(e)}", text_color="red")

    def start_update_thread(self):
        if not self.game_config.GamePath:
            self.status_label.configure(text="Set folder first!", text_color="red")
            return
        threading.Thread(target=self.perform_update, daemon=True).start()
    
    def toggle_progress(self, show: bool):
        if show:
            self.progress_bar.pack(side="bottom", pady=5)
        else:
            self.progress_bar.pack_forget()

    def perform_update(self):
        self.status_label.configure(text="Fetching latest manifest...", text_color="yellow")
        self.after(0, lambda: self.toggle_progress(True))
        self.progress_bar.set(0)
        
        url = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{self.game_config.Branch.value}/GameManifest.json"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            current_manifest = load_manifest_memory(response.content)
        except Exception as e:
            self.after(0, lambda: self.toggle_progress(False))
            self.after(0, lambda: self.status_label.configure(text="Could not fetch manifest.", text_color="red"))
            return

        self.status_label.configure(text="Downloading files...", text_color="yellow")
        files_to_download = current_manifest.Files
        total_bytes = sum(getattr(f, 'Size', 0) for f in files_to_download)
        downloaded_bytes = [0] 
        progress_lock = threading.Lock()
        
        def download_single_file(asset: GameFileInfo):
            dest = Path(self.game_config.GamePath) / asset.Path
            dest.parent.mkdir(parents=True, exist_ok=True)
            temp_dest = dest.with_suffix(dest.suffix + ".tmp")
            download_url = f"https://github.com/{REPO}/releases/download/{self.game_config.BuildTag.value}/{asset.OriginalFileName}"
            try:
                with requests.get(download_url, stream=True, timeout=15) as r:
                    r.raise_for_status()
                    with open(temp_dest, "wb") as f:
                        for chunk in r.iter_content(chunk_size=16384):
                            if chunk:
                                f.write(chunk)
                                with progress_lock:
                                    self.after(0, lambda n=asset.OriginalFileName: self.status_label.configure(text=f"Downloading: {n}"))
                                    if total_bytes > 0:
                                        downloaded_bytes[0] += len(chunk)
                                        self.after(0, lambda p=downloaded_bytes[0]/total_bytes: self.progress_bar.set(p))
                
                if os.path.exists(dest):
                    os.remove(dest)
                os.rename(temp_dest, dest)
            except Exception as e:
                if temp_dest.exists():
                    temp_dest.unlink()
                raise e
            return asset.OriginalFileName

        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(download_single_file, asset) for asset in files_to_download]
                for future in futures:
                    finished_file = future.result()
                    self.after(0, lambda n=finished_file: self.status_label.configure(text=f"Completed: {n}"))

            save_manifest(current_manifest, MANIFEST_PATH)
            self.game_manifest = current_manifest
            self.after(0, lambda: self.toggle_progress(False))
            self.after(0, lambda: self.status_label.configure(text="Update Complete!", text_color="green"))
            
        except Exception as e:
            self.after(0, lambda: self.toggle_progress(False))
            self.after(0, lambda: self.status_label.configure(text=f"Update failed", text_color="red"))
            
    def launch_game(self):
        if not self.game_config.GamePath.exists():
            return
        
        bat_path = self.game_config.GamePath / "run.bat"
        if os.path.exists(bat_path):
            subprocess.Popen(["cmd", "/c", bat_path], cwd=self.game_config.GamePath, shell=True)
            self.quit()
        else:
            self.status_label.configure(text="BlueArchive.exe and run.bat not found!", text_color="red")

if __name__ == "__main__":
    if is_admin():
        app = App()
        app.mainloop()
    else:
        run_admin()