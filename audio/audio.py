

import os
import re
import json
import pygame
import asyncio
import edge_tts
import keyboard
import webrtcvad
from configs.configs import load_config
config = load_config()
    
# VAD aggressiveness 0-3
vad = webrtcvad.Vad(3)
CHUNK = 480
first_boot= True

async def bootAudio(first_boot):
    import random
    
    
    if first_boot:
        greeting = random.choice(config["GREETINGS"])
    else:
        greeting = random.choice(config["REGREETS"])
    print(greeting)
    communicate = edge_tts.Communicate(greeting, config["TTS_VOICE"], rate=config["TTS_RATE"])
    await communicate.save("audio/BootAudio.mp3")
    pygame.mixer.music.load("audio/BootAudio.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.05)
    pygame.mixer.music.unload()

async def speak(text):
    communicate = edge_tts.Communicate(text, config["TTS_VOICE"], rate=config["TTS_RATE"])
    await communicate.save(config["OUTPUT_FILENAME"])
    pygame.mixer.music.load(config["OUTPUT_FILENAME"])
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        if keyboard.is_pressed("esc"):  # Cancel speech on ESC key
            pygame.mixer.music.stop()
            break
        await asyncio.sleep(0.05)
    pygame.mixer.music.unload()
    os.remove(config["OUTPUT_FILENAME"])

def clean_for_tts(text):

    text = re.sub(r"```.*?```", "Code example available in console.", text, flags=re.DOTALL)
    text = re.sub(r"`(.*?)`", r"\1", text)
    text = re.sub(r"https?://\S+", "link omitted.", text)
    
    return text

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