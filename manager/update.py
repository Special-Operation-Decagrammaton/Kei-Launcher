import os
import threading
import requests

from config import MANIFEST_PATH, REPO
from pathlib import Path
from lib.checker import check_game_executable, check_new_update
from manager.interface import AppInterface
from model.manifest import load_manifest_memory, save_manifest

class UpdateManager:
    def __init__(self, app: AppInterface):
        self.app = app
        self.status_timer = None
        
    def toggle_progress(self, show: bool):
        if show:
            self.app.progress_bar.pack(fill="x", side="bottom", pady=(5, 0))
        else:
            self.app.progress_bar.pack_forget()
            
    def display_status(self, text: str, text_color: str = "white", stay: bool = False, timer: int = 3000):
        if self.status_timer:
            self.app.after_cancel(self.status_timer)

        self.app.status_label.configure(text=text, text_color=text_color)
        self.app.status_label.pack(side="top", pady=(0, 5))

        if not stay:
            self.status_timer = self.app.after(timer, self.app.status_label.pack_forget)
    
    def check_updates(self):
        self.display_status(text="Checking manifest...", text_color="yellow")
        url = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{self.app.game_config.Branch.value}/GameManifest.json"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.app.remote_game_manifest = load_manifest_memory(response.content)
                textMsg, textColor = check_new_update(self.app.game_config, self.app.installed_game_manifest, self.app.remote_game_manifest)
                self.display_status(text=textMsg, text_color=textColor)
                self.app.setting_manager.update_latest_patch_text()
            else:
                self.display_status(text="No updates found.", text_color="green")
        except Exception as e:
            print(e)
            self.display_status(text=f"Error: {str(e)}", text_color="red")
    
    def start_update_thread(self):
        if not self.app.game_config.GamePath or not self.app.game_config.GamePath.exists():
            self.display_status(text="Set folder first!", text_color="red")
            self.app.btn_launch.configure(state="disabled")
            return
        threading.Thread(target=self.perform_update, daemon=True).start()
    
    def perform_update(self):
        self.app.btn_update.configure(state="disabled")
        self.app.btn_launch.configure(state="disabled")
        self.app.after(0, lambda: self.toggle_progress(True))
        self.display_status(text="Fetching latest manifest...", text_color="yellow")
        self.app.progress_bar.set(0)
        
        if not check_game_executable(self.app.game_config.GamePath):
            self.display_status(text="Set folder first!", text_color="red")
            self.app.btn_update.configure(state="normal")
            self.app.btn_launch.configure(state="disabled")
            self.app.after(0, lambda: self.toggle_progress(False))
            return
        
        url = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{self.app.game_config.Branch.value}/GameManifest.json"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self.app.remote_game_manifest = load_manifest_memory(response.content)
        except Exception as e:
            self.app.after(0, lambda: self.toggle_progress(False))
            self.app.after(0, lambda: self.display_status(text="Could not fetch manifest.", text_color="red"))
            self.app.btn_update.configure(state="normal")
            self.app.btn_launch.configure(state="normal")
            return

        self.display_status(text="Downloading files...", text_color="yellow", stay=True)
        files_to_download = self.app.remote_game_manifest.Files
        total_bytes = sum(getattr(f, 'Size', 0) for f in files_to_download)
        downloaded_so_far = 0 
        
        try:
            for asset in files_to_download:
                dest = Path(self.app.game_config.GamePath) / asset.Path
                dest.parent.mkdir(parents=True, exist_ok=True)
                temp_dest = dest.with_suffix(dest.suffix + ".tmp")
                download_url = f"https://github.com/{REPO}/releases/download/{self.app.game_config.BuildTag.value}/{asset.Hash}"
                
                self.app.after(0, lambda n=asset.OriginalFileName: self.display_status(text=f"Downloading: {n}", stay=True))

                with requests.get(download_url, stream=True, timeout=15) as r:
                    r.raise_for_status()
                    with open(temp_dest, "wb") as f:
                        for chunk in r.iter_content(chunk_size=16384):
                            if chunk:
                                f.write(chunk)
                                downloaded_so_far += len(chunk)
                                if total_bytes > 0:
                                    percent = downloaded_so_far / total_bytes
                                    self.app.after(0, lambda p=percent: self.app.progress_bar.set(p))
                
                if os.path.exists(dest):
                    os.remove(dest)
                os.rename(temp_dest, dest)
                self.app.after(0, lambda n=asset.OriginalFileName: self.display_status(text=f"Completed: {n}"))

            save_manifest(self.app.remote_game_manifest, MANIFEST_PATH)
            self.app.installed_game_manifest = self.app.remote_game_manifest
            self.app.after(0, lambda: self.toggle_progress(False))
            self.app.after(0, lambda: self.display_status(text="Update Complete!", text_color="green"))
            self.app.setting_manager.update_installed_patch_text()
            
        except Exception as e:
            print(f"Update error: {e}")
            self.app.after(0, lambda: self.toggle_progress(False))
            self.app.after(0, lambda: self.display_status(text="Update failed", text_color="red"))
        
        self.app.btn_update.configure(state="normal")
        self.app.btn_launch.configure(state="normal")
            
