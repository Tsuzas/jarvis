# OverlayWindow Create and abused by AI :)
import os
import json
import threading
import tkinter as tk
from PIL import Image, ImageTk
# IMPORTS config and loads it
from configs.configs import load_config
config = load_config()



class OverlayWindow:
    def __init__(self, image_path):
        self.image_path = image_path
        self.root = None
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.ready.wait()

    def _run(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "black")
        self.root.configure(bg="black")

        # Load all frames from the GIF
        gif = Image.open(self.image_path)
        self.frames = []
        try:
            while True:
                frame = gif.copy().convert("RGBA").resize((200, 200))
                self.frames.append(ImageTk.PhotoImage(frame))
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass

        self.label = tk.Label(self.root, bg="black")
        self.label.pack()
        self.root.geometry(f"+{self.root.winfo_screenwidth()-220}+{self.root.winfo_screenheight()-240}")
        self.root.withdraw()
        self.ready.set()

        self._animate(0)
        self.root.mainloop()

    def _animate(self, frame_index):
        if self.frames:
            self.label.config(image=self.frames[frame_index])
            next_frame = (frame_index + 1) % len(self.frames)
            self.root.after(50, self._animate, next_frame)  # 50ms per frame (~20fps)

    def show(self):
        if self.root:
            self.root.deiconify()

    def hide(self):
        if self.root:
            self.root.withdraw()

def create_tray_icon():
    import pystray

    image = Image.open("media/tray_icon.png")
    menu = pystray.Menu(
        pystray.MenuItem("Settings", open_menu),
        pystray.MenuItem("Quit", on_quit)
    )
    icon = pystray.Icon("Jarvis", image, "Jarvis Assistant", menu)
    threading.Thread(target=icon.run, daemon=True).start()

def on_quit(icon, item):
        icon.stop()
        os._exit(0)

def open_menu():

    def launch():
        settings = tk.Toplevel()
        settings.title("Jarvis Settings")
        settings.geometry("500x400")
        settings.resizable(False, False)
        settings.attributes("-topmost", True)

        tk.Label(settings, text="Jarvis Assistant", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(settings, text="App Name       |       App Path").pack()

        rows = []  # stores (name_entry, path_entry) per row

        frame = tk.Frame(settings)
        frame.pack(pady=5)

        def add_row(name="", path=""):
            row_frame = tk.Frame(frame)
            row_frame.pack(pady=2)

            name_entry = tk.Entry(row_frame, width=12)
            name_entry.insert(0, name)
            name_entry.pack(side="left", padx=5)

            path_entry = tk.Entry(row_frame, width=40)
            path_entry.insert(0, path)
            path_entry.pack(side="left", padx=5)

            rows.append((name_entry, path_entry))

            # When user types in the last empty row, add a new empty one
            def on_type(event):
                if rows and rows[-1] == (name_entry, path_entry):
                    if name_entry.get().strip() or path_entry.get().strip():
                        add_row()

            name_entry.bind("<KeyRelease>", on_type)
            path_entry.bind("<KeyRelease>", on_type)

        # Populate existing apps
        for app_name, app_path in config["APPS"].items():
            add_row(app_name, app_path)

        # Extra empty row at the end
        add_row()

        def save():
            config["APPS"].clear()
            for name_entry, path_entry in rows:
                name = name_entry.get().strip()
                path = path_entry.get().strip()
                if name and path:  # skip empty rows
                    config["APPS"][name] = path
            print("APPS updated:", config["APPS"])

            with open("configs/config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)

            settings.destroy()

        tk.Button(settings, text="Save", width=20, command=save).pack(pady=10)
        tk.Button(settings, text="Close", width=20, command=settings.destroy).pack()

        settings.mainloop()

    threading.Thread(target=launch, daemon=True).start()    


