
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

from faster_whisper import WhisperModel

# IMPORT config and loads it
import configs.configs as configs
config = configs.load_config()
# IMPORT Audio functions
import audio.audio as audio
# IMPORT UI functions
import gui.ui as ui

# Download models on first run 
openwakeword.utils.download_models()

#GLOBAL STRUFF
global audio_np

## SETUP
os.environ["PATH"] += os.pathsep + config["FFMPEG_PATH"]
pygame.mixer.init()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
overlay = ui.OverlayWindow("media/Haunter.gif")
ui.create_tray_icon()

STATE = "WAKE"

## OPENWAKEWORD + PYAUDIO + WHISPER SETUP
oww_model = audio.createWakeWordModel()
whisper_model = audio.createWhisperModel()

# 
audios, stream = audio.openAudio()

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

            audio_np = audio.audioProcess(frames)

            STATE = "PROCESS"


        elif STATE == "PROCESS":

            prompt = audio.createPrompt(audio_np, whisper_model)

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