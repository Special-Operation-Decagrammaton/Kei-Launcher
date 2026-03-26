import customtkinter as ctk

from PIL import Image
from lib.helper import resource_path
from lib.permission import is_admin, run_admin
from manager.launch import LaunchManager
from manager.setting import SettingManager
from manager.update import UpdateManager
from model.config import Branch

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._set_appearance_mode("dark")
        self.configure(fg_color="#1a1a1a")
        self.launch_manager = LaunchManager(self)
        self.setting_manager = SettingManager(self)
        self.update_manager = UpdateManager(self)
        
        self.launch_manager.setup_window()
        self.launch_manager.setup_icon()
        self.setting_manager.setup_configuration()
        
        ORANGE_COLOR = "#a66100"
        ORANGE_HOVER = "#854d00"
        BLUE_COLOR = "#3b5b92"
        BLUE_HOVER = "#2a4a75"
        GREEN_COLOR = "#137313"
        GREEN_HOVER = "#0e560e"
        GITHUB_FOREGROUND = "#c2c2c2"
        BORDER_COLOR = "#2b4569"
        
        # GitHub Logo (Top Left)
        github_icon_path = resource_path("asset/github-logo.png")
        image_data = Image.open(github_icon_path).convert("RGBA")
        self.github_image = ctk.CTkImage(light_image=image_data, dark_image=image_data, size=(40, 40))
        
        self.github_btn = ctk.CTkButton(
            self, image=self.github_image, text="",
            width=60, height=60, fg_color=GITHUB_FOREGROUND, border_width=1, border_color=BORDER_COLOR,
            hover_color=("gray70", "gray30"), command=self.launch_manager.open_github_link
        )
        self.github_btn.place(x=20, y=20)

        # Title (Top Center)
        main_title_font = ctk.CTkFont(family="Roboto", size=46, weight="bold", underline=True)
        self.main_title = ctk.CTkLabel(self, text="BA TL Launcher", font=main_title_font, fg_color="transparent")
        self.main_title.pack(pady=(20, 30))

        # Main Layout Body
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=40)
        self.body_frame.grid_columnconfigure(0, weight=1) # Left: Patches
        self.body_frame.grid_columnconfigure(1, weight=1) # Center: Branch
        self.body_frame.grid_columnconfigure(2, weight=1) # Right: Buttons

        # Column 1: Patch Info (Left)
        self.col_left = ctk.CTkFrame(self.body_frame, fg_color="transparent")
        self.col_left.grid(row=0, column=0, sticky="n")
        label_font = ctk.CTkFont(family="Roboto", size=20, weight="bold", underline=True)

        # Installed Container
        self.installed_container = ctk.CTkFrame(
            self.col_left, 
            fg_color="transparent", 
            border_width=1, 
            border_color=BORDER_COLOR, 
            corner_radius=6
        )
        self.installed_container.pack(fill="x", pady=(0, 5), padx=5)

        ctk.CTkLabel(self.installed_container, text="Installed Patch", fg_color="transparent", font=label_font).pack(pady=(10, 0))
        self.installed_date = ctk.CTkLabel(self.installed_container, text="-", font=("Roboto", 14), text_color="white")
        self.installed_date.pack()

        self.installed_note = ctk.CTkTextbox(
            self.installed_container, width=250, height=90, font=("Roboto", 13), 
            text_color="white", fg_color="transparent", border_width=0,
            activate_scrollbars=True, wrap="word"
        )
        self.installed_note.pack(pady=(0, 10), padx=10)
        self.installed_note.insert("0.0", "No patch notes available.")
        self.installed_note.configure(state="disabled")

        # Latest Container
        self.latest_container = ctk.CTkFrame(
            self.col_left, 
            fg_color="transparent", 
            border_width=1, 
            border_color=BORDER_COLOR, 
            corner_radius=6
        )
        self.latest_container.pack(fill="x", pady=5, padx=5)

        ctk.CTkLabel(self.latest_container, text="Latest Patch", fg_color="transparent", font=label_font).pack(pady=(10, 0))
        self.latest_date = ctk.CTkLabel(self.latest_container, text="-", font=("Roboto", 14), text_color="white")
        self.latest_date.pack()

        self.latest_note = ctk.CTkTextbox(
            self.latest_container, width=250, height=90, font=("Roboto", 13),
            text_color="white", fg_color="transparent", border_width=0,
            activate_scrollbars=True, wrap="word"
        )
        self.latest_note.pack(pady=(0, 10), padx=10)
        self.latest_note.insert("0.0", "No patch notes available.")
        self.latest_note.configure(state="disabled")

        # Column 2: Branch Selection (Center)
        self.col_center = ctk.CTkFrame(self.body_frame, fg_color="transparent")
        self.col_center.grid(row=0, column=1, sticky="n")

        ctk.CTkLabel(self.col_center, text="Branch", font=label_font).pack(pady=(0, 10))
        self.branch_option = ctk.CTkOptionMenu(
            self.col_center,
            values=Branch.list_values(),
            font=("Roboto", 18),
            width=220,
            height=45,
            fg_color=BLUE_COLOR,
            button_color=BLUE_COLOR,
            command=self.setting_manager.save_branch_launcher_config
        )
        self.branch_option.set(self.game_config.Branch.value if self.game_config else "Select Branch")
        self.branch_option.pack()
        
        self.branch_info_text = ctk.CTkLabel(
            self.col_center, text="Select a branch to see details.", 
            font=("Roboto", 14), text_color="gray", wraplength=200
        )
        self.branch_info_text.pack(pady=15)

        # Column 3: Action Buttons (Right)
        self.col_right = ctk.CTkFrame(self.body_frame, fg_color="transparent")
        self.col_right.grid(row=0, column=2, sticky="n")

        btn_w, btn_h = 248, 44
        # Set Folder (Blue)
        self.btn_folder = ctk.CTkButton(
            self.col_right, text="Set Folder Location", font=("Roboto", 14),
            width=btn_w, height=btn_h, fg_color=BLUE_COLOR, hover_color=BLUE_HOVER,
            command=self.setting_manager.set_game_folder
        )
        self.btn_folder.pack(pady=(0, 15))

        # Orange Stack
        orange_style = {"width": btn_w, "height": btn_h, "fg_color": ORANGE_COLOR, "hover_color": ORANGE_HOVER}
        
        self.btn_check = ctk.CTkButton(self.col_right, text="Check Update Patch", font=("Roboto", 14), **orange_style, command=self.update_manager.start_check_updates_thread)
        self.btn_check.pack(pady=5)
        
        self.btn_update = ctk.CTkButton(self.col_right, text="Install / Update Patch", font=("Roboto", 14), **orange_style, command=self.update_manager.start_update_thread)
        self.btn_update.pack(pady=5)
        
        self.btn_original = ctk.CTkButton(self.col_right, text="Install Original Patch", font=("Roboto", 14), **orange_style)
        self.btn_original.pack_forget()
        # self.btn_original.pack(pady=5)

        # Footer Section
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.pack(side="bottom", fill="x", padx=40, pady=30)

        # Download/Progress (Bottom Left)
        self.progress_container = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        self.progress_container.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.status_label = ctk.CTkLabel(self.progress_container, text="", text_color="orange", font=("Roboto", 15, "bold"))
        self.status_label.pack_forget()
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_container, height=18, width=550)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()

        # Launch Button (Bottom Right)
        self.btn_launch = ctk.CTkButton(
            self.footer_frame, text="Launch", 
            width=240, height=72, font=("Roboto", 32, "bold"),
            fg_color=GREEN_COLOR, hover_color=GREEN_HOVER,
            command=self.launch_manager.launch_game
        )
        self.btn_launch.pack(side="right")

        if not self.game_config.GamePath or not self.game_config.GamePath.exists():
            self.status_label.pack(side="top", pady=(0, 5))
            self.status_label.configure(text="Please set Game Folder first!", text_color="orange")
            self.btn_launch.configure(state="disabled")
        if self.game_config and self.game_config.Branch.value != None:
            self.setting_manager.set_branch_description(self.game_config.Branch.value)
        if self.installed_game_manifest is not None:
            self.setting_manager.update_installed_patch_text()
            self.update_manager.start_check_updates_thread()
            
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    if is_admin():
        app = App()
        app.mainloop()
    else:
        run_admin()