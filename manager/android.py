import datetime
import shutil
import subprocess
import threading
from pathlib import Path

import requests

from config import CONFIG_DIR, REPO
from manager.interface import AppInterface
from model.config import Branch
from model.i18n import t
from model.manifest import load_manifest_memory

PKG = "com.YostarJP.BlueArchive"
SUBDIR = f"Android/data/{PKG}/files/TableBundles"
ROOTS = ["/sdcard", "/storage/emulated/0", "/data/media/0"]


class AndroidManager:
    def __init__(self, app: AppInterface):
        self.app = app

    # ------------------------------------------------------------------ pure (testable) logic lol
    @staticmethod
    def find_adb():
        for c in ("adb", "adb.exe"):
            p = shutil.which(c)
            if p:
                return p
        here = Path(__file__).resolve().parent.parent  # launcher root
        for rel in ("adb.exe", "adb", "platform-tools/adb.exe", "platform-tools/adb"):
            cand = here / rel
            if cand.exists():
                return str(cand)
        return None

    @staticmethod
    def tablebundle_files(manifest):
        #manifest files stored in TableBundles (ExcelDB.db, Excel.zip).
        #the font (resources.assets) is located in BlueArchive_Data and is not included (it resides in the apk, so font lock...)
        out = []
        for f in manifest.Files:
            folder = (f.FolderPath or "").replace("\\", "/")
            if folder.endswith("TableBundles"):
                out.append(f)
        return out

    @staticmethod
    def prefix_of(finalized: str) -> str:
        return finalized.split("_")[0] + "_"

    @classmethod
    def version_ok(cls, finalized: str, device_files) -> bool:
        # true if the phone already has exactly this file (same version)
        return finalized in device_files

    # ------------------------------------------------------------------ adb
    @staticmethod
    def _adb(adb_path, serial, *args):
        cmd = [adb_path] + (["-s", serial] if serial else []) + list(args)
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        return r.returncode, r.stdout.strip(), r.stderr.strip()

    @classmethod
    def list_devices(cls, adb_path):
        cls._adb(adb_path, None, "start-server")
        _, out, _ = cls._adb(adb_path, None, "devices")
        devs = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devs.append(parts[0])
        return devs

    @classmethod
    def detect_root(cls, adb_path, serial):
        for root in ROOTS:
            d = f"{root}/{SUBDIR}"
            rc, out, err = cls._adb(adb_path, serial, "shell", "ls", d)
            if rc == 0 and "Permission denied" not in err and "No such file" not in (out + err):
                return d, out
        return None, None

    # ------------------------------------------------------------------ flow
    def start_deploy(self):
        branch = self.app.game_config.Branch
        if branch == Branch.NONE:
            self.app.update_manager.display_status(text=t("android_select_branch"), text_color="red")
            return
        self._show_confirm(
            branch.value,
            lambda: threading.Thread(target=self.perform_deploy, args=(branch.value,), daemon=True).start(),
        )

    def _status(self, key, color="yellow", stay=True, **kw):
        um = self.app.update_manager
        self.app.after(0, lambda: um.display_status(text=t(key, **kw), text_color=color, stay=stay))

    def _ensure_local(self, asset, branch_value):
        # ensures a local copy of the file (downloads the release if it is not in the cache)
        cache = Path(CONFIG_DIR) / "android_cache" / branch_value
        cache.mkdir(parents=True, exist_ok=True)
        dest = cache / str(asset.Hash)
        if dest.exists() and dest.stat().st_size > 0:
            return dest
        self._status("android_downloading", n=asset.OriginalFileName)
        url = f"https://github.com/{REPO}/releases/download/{branch_value}/{asset.Hash}"
        tmp = dest.with_suffix(".part")
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        if total > 0:
                            self.app.after(0, lambda p=done / total: self.app.progress_bar.set(p))
        tmp.replace(dest)
        return dest

    def perform_deploy(self, branch_value):
        um = self.app.update_manager

        adb_path = self.find_adb()
        if not adb_path:
            self._status("android_no_adb", "red", stay=False)
            return

        self._status("android_checking")
        devices = self.list_devices(adb_path)
        if not devices:
            self._status("android_no_device", "red", stay=False)
            return
        serial = devices[0]

        tb_dir, ls_out = self.detect_root(adb_path, serial)
        if not tb_dir:
            self._status("android_no_gamedir", "red", stay=False)
            return
        device_files = ls_out.split()

        self._status("android_fetching")
        try:
            url = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{branch_value}/PatchManifest.json"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            manifest = load_manifest_memory(r.content)
        except Exception:
            self._status("android_failed", "red", stay=False)
            return

        files = self.tablebundle_files(manifest)
        if not files:
            self._status("android_no_tables", "red", stay=False)
            return

        # version check: phone must have exactly these files
        for asset in files:
            if not self.version_ok(asset.FinalizedFileName, device_files):
                self._status("android_version_mismatch", "red", stay=False)
                return

        self.app.after(0, lambda: um.toggle_progress(True))
        self.app.after(0, lambda: self.app.progress_bar.set(0))
        try:
            backup_dir = Path(CONFIG_DIR) / "android_backup" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)

            n = len(files)
            for i, asset in enumerate(files):
                local = self._ensure_local(asset, branch_value)

                self._status("android_backing_up", n=asset.OriginalFileName)
                self._adb(adb_path, serial, "pull", f"{tb_dir}/{asset.FinalizedFileName}", str(backup_dir))

                self._status("android_pushing", n=asset.OriginalFileName)
                rc, out, err = self._adb(adb_path, serial, "push", str(local), f"{tb_dir}/{asset.FinalizedFileName}")
                if rc != 0:
                    raise RuntimeError(err or out)

                self.app.after(0, lambda p=(i + 1) / n: self.app.progress_bar.set(p))

            self.app.after(0, lambda: um.toggle_progress(False))
            self._status("android_done", "green", stay=False)
        except Exception as e:
            print(f"Android deploy error: {e}")
            self.app.after(0, lambda: um.toggle_progress(False))
            self._status("android_failed", "red", stay=False)

    # ------------------------------------------------------------------ confirmation dialog
    def _show_confirm(self, branch_value, on_yes):
        import customtkinter as ctk

        if hasattr(self, "confirm_popup") and self.confirm_popup.winfo_exists():
            self.confirm_popup.focus()
            return

        popup = ctk.CTkToplevel(self.app)
        self.confirm_popup = popup
        popup.title(t("android_confirm_title"))
        width, height = 440, 280
        sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
        popup.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")
        popup.resizable(False, False)
        popup.transient(self.app)
        try:
            self.app.launch_manager.setup_icon(popup)
        except Exception:
            pass

        ctk.CTkLabel(
            popup, text=t("android_confirm_body", branch=branch_value),
            font=("Roboto", 13), wraplength=400, justify="left",
        ).pack(pady=(20, 15), padx=20)

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        def do_yes():
            popup.destroy()
            on_yes()

        ctk.CTkButton(btn_frame, text=t("android_yes"), fg_color="#137313", hover_color="#0e560e",
                      width=120, command=do_yes).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text=t("android_cancel"), fg_color="gray", hover_color="gray40",
                      width=120, command=popup.destroy).pack(side="right", expand=True, padx=5)
