import os
import customtkinter as ctk
from PIL import Image

from lib.helper import resource_path

class KeiChan:
    IMG_W, IMG_H = 64, 94
    CLICKS_PER_CHANGE = 4

    SEQUENCE = [
        "1.png", "2.png", "3.png", "4.png",
        "5.png", "6.png", "7.png", "8.png"
    ]

    AUDIO_1 = "1.wav"
    AUDIO_2 = "2.wav"

    def __init__(self, app):
        self.app = app
        self.clicks = 0
        self.step = 0
        self.clicks_disabled = False
        self.lbl = None
        self._jobs = [] 
        self.faces = self._load_faces()
        self.ok = self.SEQUENCE[0] in self.faces

    def _load_faces(self):
        faces = {}
        for fname in self.SEQUENCE:
            try:
                path = resource_path(os.path.join("asset", "kei-chan", fname))
                img = Image.open(path)
                faces[fname] = ctk.CTkImage(light_image=img, dark_image=img, size=(self.IMG_W, self.IMG_H))
            except Exception:
                pass
        return faces

    def attach(self, parent):
        if not self.ok:
            return
            
        if self.lbl is not None and self.lbl.winfo_exists():
            self.lbl.destroy()
            
        self.lbl = ctk.CTkLabel(parent, text="", image=self.faces.get(self.SEQUENCE[self.step]), fg_color="transparent")
        self.lbl.place(relx=1.0, rely=1.0, x=-6, y=-6, anchor="se")
        self.lbl.bind("<Button-1>", lambda e: self._on_click())
        try:
            self.lbl.configure(cursor="hand2")
        except Exception:
            pass

    def _cancel_jobs(self):
        for job in self._jobs:
            try:
                self.app.after_cancel(job)
            except Exception:
                pass
        self._jobs.clear()

    def _on_click(self):
        if self.clicks_disabled:
            return
            
        self.clicks += 1
        
        if self.clicks % self.CLICKS_PER_CHANGE != 0:
            return
            
        self.step += 1
        
        if self.step <= 4:
            self._show(self.SEQUENCE[self.step])
            
            if self.step == 4:
                self.clicks_disabled = True
                
                job1 = self.app.after(1000, lambda: self._play(self.AUDIO_1))
                job2 = self.app.after(3000, self._go_to_step6)
                
                self._jobs.extend([job1, job2])

    def _go_to_step6(self):
        self.step = 5
        self._show(self.SEQUENCE[self.step])
        
        job = self.app.after(4000, self._go_to_step7)
        self._jobs.append(job)

    def _go_to_step7(self):
        self.step = 6
        self._show(self.SEQUENCE[self.step])
        
        self._play(self.AUDIO_2) 
        
        job = self.app.after(4000, self._go_to_step8)
        self._jobs.append(job)

    def _go_to_step8(self):
        self.step = 7  
        self._show(self.SEQUENCE[self.step])
        
        job = self.app.after(3000, self._revert)
        self._jobs.append(job)

    def _revert(self):
        self._cancel_jobs()
        self.clicks = 0
        self.step = 0
        self._show(self.SEQUENCE[self.step])
        self.clicks_disabled = False

    def _show(self, fname):
        img = self.faces.get(fname)
        if img is not None and self.lbl is not None:
            try:
                if self.lbl.winfo_exists():
                    self.lbl.configure(image=img)
            except Exception:
                pass

    def _play(self, wav):
        path = resource_path(os.path.join("asset", "kei-chan", wav))
        if os.path.exists(path):
            try:
                import platform
                if platform.system() == "Windows":
                    import winsound
                    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            except Exception:
                pass
