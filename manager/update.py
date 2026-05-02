import os
import threading
import requests

from config import MANIFEST_PATH, REPO, VERSION, LAUNCHER_REPO
from pathlib import Path
from lib.checker import check_game_executable, check_new_update
from manager.interface import AppInterface
from model.config import Branch
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
        def _update_ui():
            if self.status_timer:
                self.app.after_cancel(self.status_timer)

            self.app.status_label.configure(text=text, text_color=text_color)
            self.app.status_label.pack(side="top", pady=(0, 5))

            if not stay:
                self.status_timer = self.app.after(timer, self.app.status_label.pack_forget)
        
        self.app.after(0, _update_ui)
            
    def start_check_updates_thread(self):
        threading.Thread(target=self.check_updates, daemon=True).start()

    def start_check_launcher_update_thread(self, on_complete=None, on_status=None):
        threading.Thread(target=self.check_launcher_update, args=(on_complete, on_status), daemon=True).start()
    
    def check_launcher_update(self, on_complete=None, on_status=None):
        if on_status:
            self.app.after(0, lambda: on_status("Checking launcher version...", "yellow"))
        url = f"https://api.github.com/repos/{LAUNCHER_REPO}/releases/latest"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "").lstrip('v')
                release_url = data.get("html_url", f"https://github.com/{LAUNCHER_REPO}/releases/latest")
                
                def is_newer(curr, late):
                    try:
                        curr_parts = [int(x) for x in curr.split('.')]
                        late_parts = [int(x) for x in late.split('.')]
                        return late_parts > curr_parts
                    except:
                        return late != curr

                if latest_version and is_newer(VERSION, latest_version):
                    if on_status:
                        self.app.after(0, lambda: on_status(f"New Launcher v{latest_version} available!", "cyan"))
                    self.app.after(0, lambda: self.show_launcher_update_popup(latest_version, release_url, on_complete))
                else:
                    if on_status:
                        self.app.after(0, lambda: on_status("Launcher is up to date!", "green"))
                    if on_complete:
                        self.app.after(0, on_complete)
            else:
                if on_status:
                    self.app.after(0, lambda: on_status("Unable to check updates. Please check your connection.", "red"))
                if on_complete:
                    self.app.after(0, on_complete)
        except Exception as e:
            if on_status:
                self.app.after(0, lambda: on_status("Unable to check updates. Please check your connection.", "red"))
            if on_complete:
                self.app.after(0, on_complete)

    def show_launcher_update_popup(self, version, url, on_complete):
        if hasattr(self, 'update_popup') and self.update_popup.winfo_exists():
            self.update_popup.focus()
            return
            
        import customtkinter as ctk
        popup = ctk.CTkToplevel(self.app)
        self.update_popup = popup
        popup.title("Launcher Update")
        
        width, height = 300, 150
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.resizable(False, False)
        popup.transient(self.app)
        self.app.launch_manager.setup_icon(popup)

        label = ctk.CTkLabel(popup, text=f"New launcher v{version} is available!", font=("Roboto", 14))
        label.pack(pady=(20, 15))

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)

        def download():
            import webbrowser
            webbrowser.open(url)
            popup.destroy()
            if on_complete:
                on_complete()

        def later():
            popup.destroy()
            if on_complete:
                on_complete()

        btn_download = ctk.CTkButton(btn_frame, text="Download", width=100, command=download)
        btn_download.pack(side="left", expand=True)

        btn_later = ctk.CTkButton(btn_frame, text="Later", width=100, fg_color="gray", hover_color="gray40", command=later)
        btn_later.pack(side="right", expand=True)
    
    def check_updates(self):
        if self.app.game_config.Branch == Branch.NONE:
            self.app.after(0, lambda: self.display_status(text="Select a branch first!", text_color="red"))
            return
        self.app.after(0, lambda: self.display_status(text="Checking manifest...", text_color="yellow"))
        url = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{self.app.game_config.Branch.value}/PatchManifest.json"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self.app.remote_game_manifest = load_manifest_memory(response.content)
                textMsg, textColor = check_new_update(self.app.game_config, self.app.installed_game_manifest, self.app.remote_game_manifest)
                self.app.after(0, lambda: self.display_status(text=textMsg, text_color=textColor))
                self.app.after(0, self.app.setting_manager.update_latest_patch_text)
            elif response.status_code == 404:
                self.app.after(0, lambda: self.display_status(text="Failed to fetch manifest.", text_color="red"))
            else:
                self.app.after(0, lambda: self.display_status(text="No updates found.", text_color="green"))
        except Exception as e:
            print(f"Manifest fetch error: {e}")
            self.app.after(0, lambda: self.display_status(text="Check failed.", text_color="red"))
    
    def start_update_thread(self):
        if self.app.game_config.Branch == Branch.NONE:
            self.display_status(text="Select a branch first!", text_color="red")
            return
        if not self.app.game_config.GamePath or not self.app.game_config.GamePath.exists():
            self.display_status(text="Set folder first!", text_color="red")
            self.app.btn_launch.configure(state="disabled")
            return
        threading.Thread(target=self.perform_update, daemon=True).start()
    
    def perform_update(self):
        self.app.after(0, lambda: self.app.btn_folder.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_check.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_update.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_launch.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_original.configure(state="disabled"))
        self.app.after(0, lambda: self.toggle_progress(True))
        self.display_status(text="Fetching latest manifest...", text_color="yellow")
        self.app.after(0, lambda: self.app.progress_bar.set(0))
        
        if not check_game_executable(self.app.game_config.GamePath):
            self.display_status(text="Set folder first!", text_color="red")
            self.app.after(0, lambda: self.app.btn_update.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_launch.configure(state="disabled"))
            self.app.after(0, lambda: self.app.btn_original.configure(state="normal"))
            self.app.after(0, lambda: self.toggle_progress(False))
            return
        
        url = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{self.app.game_config.Branch.value}/PatchManifest.json"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            self.app.remote_game_manifest = load_manifest_memory(response.content)
        except Exception as e:
            self.app.after(0, lambda: self.toggle_progress(False))
            self.app.after(0, lambda: self.display_status(text="Could not fetch manifest.", text_color="red"))
            self.app.after(0, lambda: self.app.btn_folder.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_check.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_update.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_launch.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_original.configure(state="normal"))
            return

        self.display_status(text="Downloading files...", text_color="yellow", stay=True)
        files_to_download = self.app.remote_game_manifest.Files
        total_files = len(files_to_download)
        total_bytes = sum(getattr(f, 'Size', 0) for f in files_to_download)
        downloaded_so_far = 0 
        
        try:
            for idx, asset in enumerate(files_to_download):
                dest = Path(self.app.game_config.GamePath) / asset.FolderPath / asset.FinalizedFileName
                dest.parent.mkdir(parents=True, exist_ok=True)
                temp_dest = dest.with_suffix(dest.suffix + ".tmp")
                download_url = f"https://github.com/{REPO}/releases/download/{self.app.game_config.Branch.value}/{asset.Hash}"
                
                self.app.after(0, lambda n=asset.OriginalFileName, c=idx+1, t=total_files: self.display_status(text=f"Downloading: {n} ({c}/{t})", stay=True))

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
            print(f"{e}")
            self.app.after(0, lambda: self.toggle_progress(False))
            self.app.after(0, lambda: self.display_status(text="Update failed", text_color="red"))
        
        self.app.after(0, lambda: self.app.btn_folder.configure(state="normal"))
        self.app.after(0, lambda: self.app.btn_check.configure(state="normal"))
        self.app.after(0, lambda: self.app.btn_update.configure(state="normal"))
        self.app.after(0, lambda: self.app.btn_launch.configure(state="normal"))
        self.app.after(0, lambda: self.app.btn_original.configure(state="normal"))

    def start_uninstall_thread(self):
        if not self.app.game_config.GamePath or not self.app.game_config.GamePath.exists():
            self.display_status(text="Set folder first!", text_color="red")
            self.app.btn_launch.configure(state="disabled")
            return
        threading.Thread(target=self.perform_uninstall, daemon=True).start()

    def perform_uninstall(self):
        self.app.after(0, lambda: self.app.btn_folder.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_check.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_update.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_launch.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_original.configure(state="disabled"))
        self.app.after(0, lambda: self.toggle_progress(True))
        self.app.after(0, lambda: self.app.progress_bar.set(0))
        
        if not self.app.installed_game_manifest:
            self.display_status(text="No patch installed to uninstall.", text_color="red")
            self.app.after(0, lambda: self.app.btn_folder.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_check.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_update.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_launch.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_original.configure(state="normal"))
            self.app.after(0, lambda: self.toggle_progress(False))
            return

        self.display_status(text="Uninstalling patch...", text_color="yellow", stay=True)
        files_to_download = self.app.installed_game_manifest.Files
        total_files = len(files_to_download)
        downloaded_so_far = 0 
        
        try:
            for idx, asset in enumerate(files_to_download):
                dest = Path(self.app.game_config.GamePath) / asset.FolderPath / asset.FinalizedFileName
                dest.parent.mkdir(parents=True, exist_ok=True)
                temp_dest = dest.with_suffix(dest.suffix + ".tmp")
                download_url = f"{asset.OriginalDownloadUrl}/{asset.OriginalFileName}"
                
                self.app.after(0, lambda n=asset.OriginalFileName, c=idx+1, t=total_files: self.display_status(text=f"Reverting: {n} ({c}/{t})", stay=True))

                with requests.get(download_url, stream=True, timeout=15) as r:
                    r.raise_for_status()
                    total_bytes = int(r.headers.get('content-length', 0))
                    current_downloaded = 0
                    with open(temp_dest, "wb") as f:
                        for chunk in r.iter_content(chunk_size=16384):
                            if chunk:
                                f.write(chunk)
                                current_downloaded += len(chunk)
                                if total_bytes > 0:
                                    percent = current_downloaded / total_bytes
                                    self.app.after(0, lambda p=percent: self.app.progress_bar.set(p))
                
                if os.path.exists(dest):
                    os.remove(dest)
                os.rename(temp_dest, dest)
                self.app.after(0, lambda n=asset.OriginalFileName: self.display_status(text=f"Reverted: {n}"))

            if os.path.exists(MANIFEST_PATH):
                os.remove(MANIFEST_PATH)
            self.app.installed_game_manifest = None
            self.app.after(0, lambda: self.toggle_progress(False))
            self.app.after(0, lambda: self.display_status(text="Uninstall Complete!", text_color="green"))
            self.app.setting_manager.update_installed_patch_text()
            
        except Exception as e:
            print(f"{e}")
            self.app.after(0, lambda: self.toggle_progress(False))
            self.app.after(0, lambda: self.display_status(text="Uninstall failed", text_color="red"))
        
        self.app.after(0, lambda: self.app.btn_folder.configure(state="normal"))
        self.app.after(0, lambda: self.app.btn_check.configure(state="normal"))
        self.app.after(0, lambda: self.app.btn_update.configure(state="normal"))
        self.app.after(0, lambda: self.app.btn_launch.configure(state="normal"))
        self.app.after(0, lambda: self.app.btn_original.configure(state="normal"))
