
import os
import re
import time
import wave
import json
import pygame
import pyaudio
import asyncio
import keyboard
import edge_tts
import threading
import webrtcvad
import numpy as np
import openwakeword
import tkinter as tk
from ollama import chat
from PIL import Image, ImageTk
from openwakeword.model import Model
from faster_whisper import WhisperModel

# IMPORTS all config variables from config.py 
import configs.config as confs


# Download models on first run 
openwakeword.utils.download_models()

# VAD aggressiveness 0-3
vad = webrtcvad.Vad(3)
CHUNK = 480
first_boot= True


# OverlayWindow Create and abused by AI :)
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

async def bootAudio(first_boot):
    import random
    
    
    if first_boot:
        greeting = random.choice(confs.GREETINGS)
    else:
        greeting = random.choice(confs.REGREETS)
    print(greeting)
    communicate = edge_tts.Communicate(greeting, "en-GB-RyanNeural", rate="+35%")
    await communicate.save("audio/BootAudio.mp3")
    pygame.mixer.music.load("audio/BootAudio.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.05)
    pygame.mixer.music.unload()

def clean_for_tts(text):

    text = re.sub(r"```.*?```", "Code example available in console.", text, flags=re.DOTALL)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"https?://\S+", "link omitted.", text)
    
    return text

async def speak(text):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="+40%")
    await communicate.save(confs.OUTPUT_FILENAME)
    pygame.mixer.music.load(confs.OUTPUT_FILENAME)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        if keyboard.is_pressed("esc"):  # Cancel speech on ESC key
            pygame.mixer.music.stop()
            break
        await asyncio.sleep(0.05)
    pygame.mixer.music.unload()
    os.remove(confs.OUTPUT_FILENAME)

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
def open_menu(icon, item):

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
        for app_name, app_path in confs.APPS.items():
            add_row(app_name, app_path)

        # Extra empty row at the end
        add_row()

        def save():
            confs.APPS.clear()
            for name_entry, path_entry in rows:
                name = name_entry.get().strip()
                path = path_entry.get().strip()
                if name and path:  # skip empty rows
                    confs.APPS[name] = path
            print("APPS updated:", confs.APPS)
            settings.destroy()

        tk.Button(settings, text="Save", width=20, command=save).pack(pady=10)
        tk.Button(settings, text="Close", width=20, command=settings.destroy).pack()

        settings.mainloop()

    threading.Thread(target=launch, daemon=True).start()    

def record_until_silence(stream):
    frames = []
    silent_chunks = 0
    SILENCE_LIMIT = 30  # ~1.5 sec of silence to stop

    print("Listening...")
    started_speaking = False

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)

        is_speech = vad.is_speech(data, sample_rate=16000)

        if is_speech:
            started_speaking = True
            silent_chunks = 0
        else:
            if started_speaking:
                silent_chunks += 1

        # keep recording after user starts talking
        if started_speaking:
            frames.append(data)

        if started_speaking and silent_chunks > SILENCE_LIMIT:
            print("Silence detected, processing...")
            break
                
    return frames

## SETUP
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
pygame.mixer.init()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
overlay = OverlayWindow("media/Haunter.gif")
create_tray_icon()

STATE = "WAKE"

## OPENWAKEWORD + PYAUDIO + WHISPER SETUP
oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")

audio = pyaudio.PyAudio()
stream = audio.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer= CHUNK,
    input_device_index=3
)

loop.run_until_complete(bootAudio(first_boot=True))

print("Listening for 'Hey Jarvis'...")

try:
    while True:

        if STATE == "WAKE":
            raw = stream.read(CHUNK, exception_on_overflow=False)
            pcm = np.frombuffer(raw, dtype=np.int16)
            prediction = oww_model.predict(pcm)
            time.sleep(0.02) 
            if prediction["hey_jarvis"] > 0.5:
                print("Hey Jarvis detected!")
                oww_model.reset()
                overlay.show()
                STATE = "LISTEN"
                loop.run_until_complete(bootAudio(first_boot=False))


        elif STATE == "LISTEN":
            pygame.mixer.Sound("audio/dings/Palumm.mp3").play()
            frames = record_until_silence(stream)

            if not frames or len(frames) < 15:
                print("Ignored audio")
                STATE = "LISTEN"
                continue

            audio_bytes = b"".join(frames)
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_np = audio_np.astype(np.float32) / 32768.0    
            wf = wave.open(confs.OUTPUT_FILENAME, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(audio_bytes)
            wf.close()

            STATE = "PROCESS"


        elif STATE == "PROCESS":
            segments, _ = whisper_model.transcribe(confs.OUTPUT_FILENAME)
            prompt = " ".join(s.text for s in segments)
            prompt = prompt.strip()

            if not prompt:
                print("Empty transcription ignored")
                STATE = "LISTEN"
                continue
            print("\nYou said:", prompt)
            

            # second call - intent only
            intentResponse = chat(
                model='mistral:7b',
                messages=[
                    {'role': 'system', 'content': confs.INTENT_PROMPT},
                    {'role': 'user', 'content': prompt}
                ]
            )
            raw = intentResponse.get("message", {}).get("content", "")
            print ("Raw intent response:", raw)
            try:
                intent = json.loads(raw)
            except json.JSONDecodeError:
                print("Invalid model output:", raw)
                intent = {}

            action = intent.get("action")
            target = intent.get("target")

            print("Intent detected:", action, "Target:", target)

            if action == "open_app" and target in confs.APPS:
                print(f"Opening {target}...")
                os.startfile(confs.APPS[target])

            elif action == "clip":
                keyboard.send("left_alt + f10")

            elif action == "screen_share":
                keyboard.send('shift+l+p')

            elif action == "open_settings":
                open_menu(None, None)

            elif action == "exit":
                print("Returning to wake word detection...")

            aiResponse = chat(
                #DESKTOP mistral:7b, LAPTOP tinylamma
                model='mistral:7b',
                messages=[
                    {'role': 'system', 'content': confs.SYSTEM_PROMPT},
                    {'role': 'user', 'content': prompt}
                ]
            )

            response_text = aiResponse['message']['content']
            print("Jarvis:", response_text)

            cleaned_text = clean_for_tts(response_text)
            #CLEANSED TEXT TTS'ed
            loop.run_until_complete(speak(cleaned_text))

            overlay.hide()
            STATE = "WAKE"
    
        else:
            overlay.hide()

finally:
    stream.stop_stream()
    stream.close()
    audio.terminate()
    loop.close()