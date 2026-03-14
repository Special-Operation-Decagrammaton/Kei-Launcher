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
        self.launch_manager = LaunchManager(self)
        self.setting_manager = SettingManager(self)
        self.update_manager = UpdateManager(self)
        
        self.launch_manager.setup_window()
        self.launch_manager.setup_icon()
        self.setting_manager.setup_configuration()
        
        # App Repo
        github_icon_path = resource_path("asset/github-logo.png")
        image_data = Image.open(github_icon_path).convert("RGBA")
        self.github_image = ctk.CTkImage(
            light_image=image_data,
            dark_image=image_data,
            size=(30, 30)
        )
        self.github_btn = ctk.CTkButton(
            self,
            image=self.github_image,
            text="",
            width=30,
            height=30,
            fg_color="transparent", 
            hover_color=("gray70", "gray30"),
            command=self.launch_manager.open_github_link
        )
        self.github_btn.place(x=10, y=10)

        # App Label
        self.label = ctk.CTkLabel(self, text="BA TL Launcher", font=("Roboto", 36, "bold"))
        self.label.pack(pady=30)
        
        # Description
        self.description = ctk.CTkLabel(
            self,
            text="Branch Selection\n\nMain branch is updated up to global version of the game.\nTranslation branch is the same as main branch, but with more recent/community added translations.",
            font=("Roboto", 14),
            justify="left"
        )
        self.description.pack(pady=10, fill="both")
        
        # Branch Selection UI
        self.branch_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.branch_frame.pack(pady=10, padx=20)
        self.branch_description = ctk.CTkLabel(
            self.branch_frame,
            text="Select Branch:",
            font=("Roboto", 14))
        self.branch_description.pack(side="left", padx=(0, 10))
        self.branch_option = ctk.CTkOptionMenu(
            master=self.branch_frame,
            values=Branch.list_values(),
            width=200,
            command=self.setting_manager.save_branch_launcher_config)
        self.branch_option.set(self.game_config.Branch.value)
        self.branch_option.pack(side="right")

        # Status / Progress UI
        self.progress_bar = ctk.CTkProgressBar(self, width=750)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=("Roboto", 14)
        )
        self.progress_bar.pack_forget()

        # Button Container (Bottom)
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(side="bottom", fill="x", padx=30, pady=(5, 20))

        # Left Buttons
        self.btn_check = ctk.CTkButton(
            self.button_frame,
            text="Check Asset Update",
            width=120,
            height=50,
            command=self.update_manager.check_updates)
        self.btn_check.pack(side="left", padx=5)

        self.btn_folder = ctk.CTkButton(
            self.button_frame,
            text="Set Game Folder",
            width=120,
            height=50,
            command=self.setting_manager.set_game_folder)
        self.btn_folder.pack(side="left", padx=5)

        # Right Buttons
        self.btn_launch = ctk.CTkButton(
            self.button_frame,
            text="Launch",
            font=("Roboto", 24, "bold"),
            width=225,
            height=60,
            fg_color="green",
            hover_color="darkgreen",
            command=self.launch_manager.launch_game)
        self.btn_launch.pack(side="right", padx=5)

        self.btn_update = ctk.CTkButton(
            self.button_frame,
            text="Update Asset",
            width=125,
            height=50,
            command=self.update_manager.start_update_thread)
        self.btn_update.pack(side="right", padx=5)

        if not self.game_config or not self.game_config.GamePath.exists():
            self.status_label.configure(text="Please set Game Folder first!", text_color="orange")
            
if __name__ == "__main__":
    if is_admin():
        app = App()
        app.mainloop()
    else:
        run_admin()