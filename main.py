
import os
import time
import wave
import json
import pygame
import pyaudio
import asyncio
import keyboard
import numpy as np
import openwakeword
from ollama import chat
from openwakeword.model import Model
from faster_whisper import WhisperModel
import configs.configs as configs
config = configs.load_config()

# IMPORT Audio functions
import audio.audio as audio
# IMPORT UI functions
import gui.ui as ui

# Download models on first run 
openwakeword.utils.download_models()


## SETUP
os.environ["PATH"] += os.pathsep + config["FFMPEG_PATH"]
pygame.mixer.init()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
overlay = ui.OverlayWindow("media/Haunter.gif")
ui.create_tray_icon()

STATE = "WAKE"

## OPENWAKEWORD + PYAUDIO + WHISPER SETUP
oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")

audios = pyaudio.PyAudio()
stream = audios.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer= audio.CHUNK,
    input_device_index = config["MICROPHONE_INDEX"]
)

loop.run_until_complete(audio.bootAudio(first_boot=True))

print("Listening for 'Hey Jarvis'...")

try:
    while True:

        if STATE == "WAKE":
            raw = stream.read(audio.CHUNK, exception_on_overflow=False)
            pcm = np.frombuffer(raw, dtype=np.int16)
            prediction = oww_model.predict(pcm)
            time.sleep(0.02) 
            if prediction["hey_jarvis"] > 0.5:
                print("Hey Jarvis detected!")
                oww_model.reset()
                overlay.show()
                STATE = "LISTEN"
                loop.run_until_complete(audio.bootAudio(first_boot=False))


        elif STATE == "LISTEN":
            pygame.mixer.Sound("audio/dings/Palumm.mp3").play()
            frames = audio.record_until_silence(stream)

            if not frames or len(frames) < 15:
                print("Ignored audio")
                STATE = "LISTEN"
                continue

            audio_bytes = b"".join(frames)
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_np = audio_np.astype(np.float32) / 32768.0    
            wf = wave.open(config["OUTPUT_FILENAME"], 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(audios.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(audio_bytes)
            wf.close()

            STATE = "PROCESS"


        elif STATE == "PROCESS":
            segments, _ = whisper_model.transcribe(config["OUTPUT_FILENAME"])
            prompt = " ".join(s.text for s in segments)
            prompt = prompt.strip()

            if not prompt:
                print("Empty transcription ignored")
                STATE = "LISTEN"
                continue
            print("\nYou said:", prompt)
            

            # second call - intent only
            intentResponse = chat(
                model= config["MODEL"],
                messages=[
                    {'role': 'system', 'content': config["INTENT_PROMPT"]},
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

            if action == "open_app" and target in config["APPS"]:
                print(f"Opening {target}...")
                os.startfile(config["APPS"][target])

            elif action == "clip":
                keyboard.send("left_alt + f10")

            elif action == "screen_share":
                keyboard.send('shift+l+p')

            elif action == "open_settings":
                ui.open_menu()

            elif action == "exit":
                print("Returning to wake word detection...")

            aiResponse = chat(
                #DESKTOP mistral:7b
                model = config["MODEL"],
                messages=[
                    {'role': 'system', 'content': config["SYSTEM_PROMPT"]},
                    {'role': 'user', 'content': prompt}
                ]
            )

            response_text = aiResponse['message']['content']
            print("Jarvis:", response_text)

            cleaned_text = audio.clean_for_tts(response_text)
            #CLEANSED TEXT TTS'ed
            loop.run_until_complete(audio.speak(cleaned_text))

            overlay.hide()
            STATE = "WAKE"
    
        else:
            overlay.hide()

finally:
    stream.stop_stream()
    stream.close()
    audios.terminate()
    loop.close()