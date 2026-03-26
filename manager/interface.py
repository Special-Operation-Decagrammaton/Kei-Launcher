from typing import Any, Protocol
import customtkinter as ctk

from model.config import LauncherConfig
from model.manifest import GameManifest

class AppInterface(Protocol):
    launch_manager: Any
    setting_manager: Any
    update_manager: Any
        
    game_config: LauncherConfig
    installed_game_manifest: GameManifest
    remote_game_manifest: GameManifest
    
    # UI Elements: Top Level
    github_btn: ctk.CTkButton
    main_title: ctk.CTkLabel
    
    # UI Elements: Main Body Containers
    body_frame: ctk.CTkFrame
    col_left: ctk.CTkFrame
    col_center: ctk.CTkFrame
    col_right: ctk.CTkFrame

    # UI Elements: Patch Info (Left Column)
    installed_container: ctk.CTkFrame
    installed_date: ctk.CTkLabel
    installed_note: ctk.CTkTextbox
    
    latest_container: ctk.CTkFrame
    latest_date: ctk.CTkLabel
    latest_note: ctk.CTkTextbox
    
    # UI Elements: Branch Selection (Center Column)
    branch_option: ctk.CTkOptionMenu
    branch_info_text: ctk.CTkLabel
    
    # UI Elements: Action Buttons (Right Column)
    btn_folder: ctk.CTkButton
    btn_check: ctk.CTkButton
    btn_update: ctk.CTkButton
    btn_original: ctk.CTkButton
    
    # UI Elements: Footer & Progress
    footer_frame: ctk.CTkFrame
    progress_container: ctk.CTkFrame
    status_label: ctk.CTkLabel
    progress_bar: ctk.CTkProgressBar
    btn_launch: ctk.CTkButton