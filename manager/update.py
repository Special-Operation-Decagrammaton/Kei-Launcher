import os
import threading
import requests
import tempfile

from config import MANIFEST_PATH, REPO, VERSION, LAUNCHER_REPO, get_r2_url, get_bundle_source
from pathlib import Path
from lib.checker import check_game_executable, check_new_update
from lib.image_patcher import ImagePatcher
from manager.interface import AppInterface
from model.config import Branch
from model.manifest import load_manifest_memory, save_manifest
from model.i18n import t

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

class UpdateManager:
    def __init__(self, app: AppInterface):
        self.app = app
        self.status_timer = None
        self.is_downloading = False
        self.is_cancelled = False
        self.current_response = None

    def _set_launch_button_to_cancel(self):
        self.app.btn_launch.configure(
            text=t("cancel"),
            fg_color=getattr(self.app, "RED_COLOR", "#a62b2b"),
            hover_color=getattr(self.app, "RED_HOVER", "#852222"),
            font=("Roboto", 26, "bold"),
            command=self.cancel_download,
            state="normal"
        )

    def _restore_launch_button(self):
        can_launch = (
            bool(self.app.game_config)
            and self.app.game_config.GamePath is not None
            and self.app.game_config.GamePath.exists()
            and check_game_executable(self.app.game_config.GamePath)
        )
        self.app.btn_launch.configure(
            text=t("launch"),
            fg_color=getattr(self.app, "GREEN_COLOR", "#137313"),
            hover_color=getattr(self.app, "GREEN_HOVER", "#0e560e"),
            font=("Roboto", 32, "bold"),
            command=self.app.launch_manager.launch_game,
            state="normal" if can_launch else "disabled"
        )

    def cancel_download(self):
        if not self.is_downloading:
            return
        self.is_cancelled = True
        self.display_status(text=t("st_cancelling"), text_color="orange", stay=True)
        if self.current_response:
            try:
                self.current_response.close()
            except Exception:
                pass
        
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
        if not self.app.game_config.CheckUpdateOnLaunch:
            if on_complete:
                self.app.after(0, on_complete)
            return
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
    
    def fetch_combined_manifest(self, branch_value: str):
        github_url = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{branch_value}/PatchManifest.json"
        
        main_manifest = None
        # 1. Fetch Primary Text Translation Manifest from GitHub
        try:
            resp = requests.get(github_url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                main_manifest = load_manifest_memory(resp.content)
        except Exception as e:
            print(f"Failed to fetch GitHub translation manifest: {e}")

        # 2. Fetch Image Bundle Manifest from Cloudflare R2
        r2_url = get_r2_url(branch_value)
        if r2_url:
            r2_manifest = None
            for url in [f"{r2_url.rstrip('/')}/PatchManifest.json", f"{r2_url.rstrip('/')}/manifest.json"]:
                try:
                    r = requests.get(url, headers=HEADERS, timeout=10)
                    if r.status_code == 200:
                        r2_manifest = load_manifest_memory(r.content)
                        break
                except Exception:
                    pass
            
            if r2_manifest:
                for f in r2_manifest.Files:
                    if not getattr(f, 'DownloadKey', ''):
                        dirname = f.FolderPath.replace("BlueArchive_Data/StreamingAssets/", "").replace("BlueArchive_Data/StreamingAssets", "").strip("/\\")
                        f.DownloadKey = f"{dirname}/{f.FinalizedFileName}" if dirname else f.FinalizedFileName

                if main_manifest:
                    # Merge image bundles into GitHub translation manifest
                    # Keep GitHub's official PatchNote, UpdateDate, and StringVersion!
                    existing_keys = {f"{f.FolderPath}/{f.FinalizedFileName}" for f in main_manifest.Files}
                    for f in r2_manifest.Files:
                        if f"{f.FolderPath}/{f.FinalizedFileName}" not in existing_keys:
                            main_manifest.Files.append(f)
                else:
                    main_manifest = r2_manifest
                    main_manifest.PatchNote = ""

        if main_manifest:
            if main_manifest.PatchNote and ("Generated by BA-TL-IMAGE" in main_manifest.PatchNote or "Cloudflare R2" in main_manifest.PatchNote):
                main_manifest.PatchNote = ""

        return main_manifest

    def check_updates(self):
        if self.app.game_config.Branch == Branch.NONE:
            self.app.after(0, lambda: self.display_status(text=t("st_select_branch"), text_color="red"))
            return
        self.app.after(0, lambda: self.display_status(text=t("st_checking"), text_color="white"))
        
        manifest = self.fetch_combined_manifest(self.app.game_config.Branch.value)
        if manifest:
            self.app.remote_game_manifest = manifest
            textMsg, textColor = check_new_update(self.app.game_config, self.app.installed_game_manifest, self.app.remote_game_manifest)
            self.app.after(0, lambda: self.display_status(text=textMsg, text_color=textColor))
            self.app.after(0, self.app.setting_manager.update_latest_patch_text)
        else:
            self.app.after(0, lambda: self.display_status(text=t("st_fetch_fail"), text_color="red"))
    
    def start_update_thread(self):
        if self.app.game_config.Branch == Branch.NONE:
            self.display_status(text=t("st_select_branch"), text_color="red")
            return
        if not self.app.game_config.GamePath or not self.app.game_config.GamePath.exists():
            self.display_status(text=t("st_set_folder"), text_color="red")
            self.app.btn_launch.configure(state="disabled")
            return
        threading.Thread(target=self.perform_update, daemon=True).start()
    
    def perform_update(self):
        self.is_downloading = True
        self.is_cancelled = False
        self.current_response = None

        self.app.after(0, lambda: self.app.btn_folder.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_check.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_update.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_original.configure(state="disabled"))
        self.app.after(0, lambda: self.app.branch_option.configure(state="disabled"))
        self.app.after(0, self._set_launch_button_to_cancel)
        self.app.after(0, lambda: self.toggle_progress(True))
        self.display_status(text="Fetching latest manifest...", text_color="white")
        self.app.progress_bar.set(0)

        temp_dest = None
        temp_zip = None

        try:
            if not check_game_executable(self.app.game_config.GamePath):
                self.display_status(text=t("st_set_folder"), text_color="red")
                self.app.after(0, lambda: self.toggle_progress(False))
                return

            r2_url = get_r2_url(self.app.game_config.Branch.value)
            manifest = self.fetch_combined_manifest(self.app.game_config.Branch.value)
            if not manifest:
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_fetch_fail"), text_color="red")
                return

            if self.is_cancelled:
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_cancelled"), text_color="orange")
                return

            self.app.remote_game_manifest = manifest

            self.display_status(text="Downloading translation files...", text_color="white", stay=True)
            files_to_download = [f for f in self.app.remote_game_manifest.Files if not f.OriginalFileName.lower().endswith(".bundle")]
            total_files = len(files_to_download)
            total_bytes = sum(getattr(f, 'Size', 0) for f in files_to_download)
            downloaded_so_far = 0 

            # 1. Download Text Translation Files from GitHub
            for idx, asset in enumerate(files_to_download):
                if self.is_cancelled:
                    break

                dest = Path(self.app.game_config.GamePath) / asset.FolderPath / asset.FinalizedFileName
                dest.parent.mkdir(parents=True, exist_ok=True)
                temp_dest = dest.with_suffix(dest.suffix + ".tmp")

                download_url = f"https://github.com/{REPO}/releases/download/{self.app.game_config.Branch.value}/{asset.Hash}"
                display_name = asset.OriginalFileName
                self.app.after(0, lambda n=display_name, c=idx+1, t=total_files: self.display_status(text=f"Downloading: {n} ({c}/{t})", stay=True))

                try:
                    with requests.get(download_url, headers=HEADERS, stream=True, timeout=15) as r:
                        self.current_response = r
                        r.raise_for_status()
                        with open(temp_dest, "wb") as f:
                            for chunk in r.iter_content(chunk_size=16384):
                                if self.is_cancelled:
                                    break
                                if chunk:
                                    f.write(chunk)
                                    downloaded_so_far += len(chunk)
                                    if total_bytes > 0:
                                        percent = downloaded_so_far / total_bytes
                                        self.app.after(0, lambda p=percent: self.app.progress_bar.set(p))
                finally:
                    self.current_response = None

                if self.is_cancelled:
                    if temp_dest and os.path.exists(temp_dest):
                        try:
                            os.remove(temp_dest)
                        except Exception:
                            pass
                    temp_dest = None
                    break

                if os.path.exists(dest):
                    os.remove(dest)
                os.rename(temp_dest, dest)
                temp_dest = None
                self.app.after(0, lambda n=display_name: self.display_status(text=f"Completed: {n}"))

            # 2. Download and Inject Translated Images (if enabled)
            if not self.is_cancelled and getattr(self.app.game_config, "DownloadImages", False) and r2_url:
                map_url = f"{r2_url.rstrip('/')}/image_bundle_map.json"
                zip_url = f"{r2_url.rstrip('/')}/images.zip"

                self.app.after(0, lambda: self.display_status(text="Fetching image map...", text_color="white", stay=True))
                map_resp = requests.get(map_url, headers=HEADERS, timeout=10)
                if not self.is_cancelled and map_resp.status_code == 200:
                    map_data = map_resp.json()
                    temp_zip = Path(tempfile.gettempdir()) / "ba_images_patch.zip"

                    self.app.after(0, lambda: self.display_status(text="Downloading: English Images...", text_color="white", stay=True))
                    try:
                        with requests.get(zip_url, headers=HEADERS, stream=True, timeout=30) as r:
                            self.current_response = r
                            r.raise_for_status()
                            zip_total = int(r.headers.get('content-length', 0))
                            zip_downloaded = 0
                            with open(temp_zip, "wb") as zf:
                                for chunk in r.iter_content(chunk_size=65536):
                                    if self.is_cancelled:
                                        break
                                    if chunk:
                                        zf.write(chunk)
                                        zip_downloaded += len(chunk)
                                        if zip_total > 0:
                                            percent = zip_downloaded / zip_total
                                            mb_cur = zip_downloaded / (1024 * 1024)
                                            mb_tot = zip_total / (1024 * 1024)
                                            self.app.after(0, lambda p=percent, c=mb_cur, t=mb_tot: (
                                                self.app.progress_bar.set(p),
                                                self.display_status(text=f"Downloading: English Images ({c:.1f}/{t:.1f} MB)", text_color="white", stay=True)
                                            ))
                    finally:
                        self.current_response = None

                    if self.is_cancelled:
                        if temp_zip and temp_zip.exists():
                            try:
                                os.remove(temp_zip)
                            except Exception:
                                pass
                    else:
                        # Patch textures directly into local game bundles
                        def update_patch_progress(status_text, percent):
                            self.app.after(0, lambda s=status_text: self.display_status(text=s, text_color="white", stay=True))
                            self.app.after(0, lambda p=percent: self.app.progress_bar.set(p))

                        ImagePatcher.patch(
                            game_path=self.app.game_config.GamePath,
                            images_zip_path=temp_zip,
                            map_data=map_data,
                            on_progress=update_patch_progress,
                            cancel_check=lambda: self.is_cancelled
                        )

                        if temp_zip.exists():
                            try:
                                os.remove(temp_zip)
                            except Exception:
                                pass
            elif not self.is_cancelled and not getattr(self.app.game_config, "DownloadImages", False):
                # If image patch is disabled, revert any existing image backups to original Japanese
                if ImagePatcher.has_backup(self.app.game_config.GamePath):
                    def update_revert_progress(status_text, percent):
                        self.app.after(0, lambda s=status_text: self.display_status(text=s, text_color="white", stay=True))
                        self.app.after(0, lambda p=percent: self.app.progress_bar.set(p))

                    ImagePatcher.revert(
                        game_path=self.app.game_config.GamePath,
                        on_progress=update_revert_progress,
                        cancel_check=lambda: self.is_cancelled
                    )

            if self.is_cancelled:
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_cancelled"), text_color="orange")
            else:
                save_manifest(self.app.remote_game_manifest, MANIFEST_PATH)
                self.app.installed_game_manifest = self.app.remote_game_manifest
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_update_done"), text_color="green")
                self.app.after(0, self.app.setting_manager.update_installed_patch_text)

        except Exception as e:
            if self.is_cancelled:
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_cancelled"), text_color="orange")
            else:
                print(f"{e}")
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_update_fail"), text_color="red")
        finally:
            if temp_dest and os.path.exists(temp_dest):
                try:
                    os.remove(temp_dest)
                except Exception:
                    pass
            if temp_zip and os.path.exists(temp_zip):
                try:
                    os.remove(temp_zip)
                except Exception:
                    pass
            self.current_response = None
            self.is_downloading = False
            self.is_cancelled = False
            self.app.after(0, self._restore_launch_button)
            self.app.after(0, lambda: self.app.btn_folder.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_check.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_update.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_original.configure(state="normal"))
            self.app.after(0, lambda: self.app.branch_option.configure(state="normal"))

    def start_uninstall_thread(self):
        if not self.app.game_config.GamePath or not self.app.game_config.GamePath.exists():
            self.display_status(text=t("st_set_folder"), text_color="red")
            self.app.btn_launch.configure(state="disabled")
            return
        threading.Thread(target=self.perform_uninstall, daemon=True).start()

    def perform_uninstall(self):
        self.is_downloading = True
        self.is_cancelled = False
        self.current_response = None

        self.app.after(0, lambda: self.app.btn_folder.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_check.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_update.configure(state="disabled"))
        self.app.after(0, lambda: self.app.btn_original.configure(state="disabled"))
        self.app.after(0, lambda: self.app.branch_option.configure(state="disabled"))
        self.app.after(0, self._set_launch_button_to_cancel)
        self.app.after(0, lambda: self.toggle_progress(True))
        self.app.after(0, lambda: self.app.progress_bar.set(0))

        temp_dest = None

        try:
            if not self.app.installed_game_manifest and not ImagePatcher.has_backup(self.app.game_config.GamePath):
                self.display_status(text="No patch installed to uninstall.", text_color="red")
                self.app.after(0, lambda: self.toggle_progress(False))
                return

            self.display_status(text="Uninstalling patch...", text_color="white", stay=True)
            files_to_download = (self.app.installed_game_manifest.Files if self.app.installed_game_manifest and self.app.installed_game_manifest.Files else [])
            total_files = len(files_to_download)

            for idx, asset in enumerate(files_to_download):
                if self.is_cancelled:
                    break
                if not asset.OriginalDownloadUrl:
                    continue
                dest = Path(self.app.game_config.GamePath) / asset.FolderPath / asset.FinalizedFileName
                dest.parent.mkdir(parents=True, exist_ok=True)
                temp_dest = dest.with_suffix(dest.suffix + ".tmp")
                download_url = f"{asset.OriginalDownloadUrl}/{asset.OriginalFileName}"

                display_name = "English Images" if (asset.OriginalFileName.lower().endswith(".bundle") or getattr(asset, 'DownloadKey', '')) else asset.OriginalFileName
                self.app.after(0, lambda n=display_name, c=idx+1, t=total_files: self.display_status(text=f"Reverting: {n} ({c}/{t})", stay=True))

                try:
                    with requests.get(download_url, headers=HEADERS, stream=True, timeout=15) as r:
                        self.current_response = r
                        r.raise_for_status()
                        total_bytes = int(r.headers.get('content-length', 0))
                        current_downloaded = 0
                        with open(temp_dest, "wb") as f:
                            for chunk in r.iter_content(chunk_size=16384):
                                if self.is_cancelled:
                                    break
                                if chunk:
                                    f.write(chunk)
                                    current_downloaded += len(chunk)
                                    if total_bytes > 0:
                                        percent = current_downloaded / total_bytes
                                        self.app.after(0, lambda p=percent: self.app.progress_bar.set(p))
                finally:
                    self.current_response = None

                if self.is_cancelled:
                    if temp_dest and os.path.exists(temp_dest):
                        try:
                            os.remove(temp_dest)
                        except Exception:
                            pass
                    temp_dest = None
                    break

                if os.path.exists(dest):
                    os.remove(dest)
                os.rename(temp_dest, dest)
                temp_dest = None
                self.app.after(0, lambda n=display_name: self.display_status(text=f"Reverted: {n}"))

            # 2. Revert Image Bundles from local .bundle.bak
            if not self.is_cancelled and ImagePatcher.has_backup(self.app.game_config.GamePath):
                self.app.after(0, lambda: self.display_status(text="Reverting: English Images...", text_color="white", stay=True))
                def update_revert_progress(status_text, percent):
                    self.app.after(0, lambda s=status_text: self.display_status(text=s, text_color="white", stay=True))
                    self.app.after(0, lambda p=percent: self.app.progress_bar.set(p))

                ImagePatcher.revert(
                    game_path=self.app.game_config.GamePath,
                    on_progress=update_revert_progress,
                    cancel_check=lambda: self.is_cancelled
                )

            if self.is_cancelled:
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_cancelled"), text_color="orange")
            else:
                if os.path.exists(MANIFEST_PATH):
                    os.remove(MANIFEST_PATH)
                self.app.installed_game_manifest = None
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_uninstall_done"), text_color="green")
                self.app.after(0, self.app.setting_manager.update_installed_patch_text)

        except Exception as e:
            if self.is_cancelled:
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_cancelled"), text_color="orange")
            else:
                print(f"{e}")
                self.app.after(0, lambda: self.toggle_progress(False))
                self.display_status(text=t("st_uninstall_fail"), text_color="red")
        finally:
            if temp_dest and os.path.exists(temp_dest):
                try:
                    os.remove(temp_dest)
                except Exception:
                    pass
            self.current_response = None
            self.is_downloading = False
            self.is_cancelled = False
            self.app.after(0, self._restore_launch_button)
            self.app.after(0, lambda: self.app.btn_folder.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_check.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_update.configure(state="normal"))
            self.app.after(0, lambda: self.app.btn_original.configure(state="normal"))
            self.app.after(0, lambda: self.app.branch_option.configure(state="normal"))
