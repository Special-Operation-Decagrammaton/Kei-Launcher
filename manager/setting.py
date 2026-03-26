import os

from pathlib import Path
from tkinter import filedialog

from config import CONFIG_DIR, CONFIG_PATH, MANIFEST_PATH
from lib.checker import check_game_executable
from manager.interface import AppInterface
from model.config import Branch, BuildTag, Language, LauncherConfig, load_config, save_config
from model.manifest import load_manifest

class SettingManager:
    def __init__(self, app: AppInterface):
        self.app = app
        
    def setup_configuration(self):
        self.app.game_config = LauncherConfig(
            GamePath=None,
            Language=Language.EN.value,
            Branch=Branch.MAIN.value,
            BuildTag=BuildTag.LATEST.value,
            CloseOnLaunch=True
        )
        self.app.installed_game_manifest = None
        self.app.remote_game_manifest = None
        self.load_launcher_config()
    
    def load_launcher_config(self):
        if os.path.exists(CONFIG_PATH):
            self.app.game_config = load_config(CONFIG_PATH)
        if os.path.exists(MANIFEST_PATH):
            self.app.installed_game_manifest = load_manifest(MANIFEST_PATH)
            
    def save_branch_launcher_config(self, branch_str: str):
        selected_branch = Branch(branch_str)
        tag_mapping = {
            Branch.MAIN: BuildTag.LATEST,
            Branch.TRANSLATION: BuildTag.TRANSLATION
        }
        
        selected_tag = tag_mapping.get(selected_branch, BuildTag.LATEST)
        
        self.app.game_config.Branch = selected_branch
        self.app.game_config.BuildTag = selected_tag
        self.set_branch_description(branch_str)
        
        save_config(self.app.game_config, CONFIG_PATH)
        self.app.update_manager.display_status(text=f"Branch set to {selected_branch.value} ({selected_tag.value})", text_color="green")
    
    def set_branch_description(self, branch_str: str):
        selected_branch = Branch(branch_str)
        descriptions = {
            Branch.MAIN: "Match with the global version of the game.",
            Branch.TRANSLATION: "Community translations with more frequent updates.",
        }
        new_description = descriptions.get(selected_branch, "Select a branch to see details.")
        self.app.branch_info_text.configure(text=new_description)
        
    def update_installed_patch_text(self):
        manifest = self.app.installed_game_manifest
        update_date = (manifest.UpdateDate if manifest else "-") or "-"
        update_note = (manifest.PatchNote if manifest else "No patch notes available.") or "No patch notes available."
        self.app.installed_date.configure(text=update_date)
        self.app.installed_note.configure(state="normal")
        self.app.installed_note.delete("0.0", "end")
        self.app.installed_note.insert("0.0", update_note)
        self.app.installed_note.configure(state="disabled")
        
    def update_latest_patch_text(self):
        manifest = self.app.remote_game_manifest
        update_date = (manifest.UpdateDate if manifest else "-") or "-"
        update_note = (manifest.PatchNote if manifest else "No patch notes available.") or "No patch notes available."
        self.app.latest_date.configure(text=update_date)
        self.app.latest_note.configure(state="normal")
        self.app.latest_note.delete("0.0", "end")
        self.app.latest_note.insert("0.0", update_note)
        self.app.latest_note.configure(state="disabled")
    
    def set_game_folder(self):
        folder = Path(filedialog.askdirectory(title="Select BlueArchive_JP Folder"))
        print(folder)
        if folder:
            if check_game_executable(folder):
                if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
                self.app.game_config.GamePath = folder
                save_config(self.app.game_config, CONFIG_PATH)
                self.app.update_manager.display_status(text=f"Path set: {folder}", text_color="green")
                self.app.btn_launch.configure(state="normal")
            else:
                self.app.update_manager.display_status(text="BlueArchive.exe and run.bat not found!", text_color="red")
