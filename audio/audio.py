

import os
import re
from typing_extensions import Literal
from faster_whisper import WhisperModel
import pygame
import asyncio
import pyaudio
import edge_tts
import keyboard
import webrtcvad
from openwakeword.model import Model
import numpy as np
from pyaudio import paInt16
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

def openAudio():
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format = pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer= CHUNK,
        input_device_index = config["MICROPHONE_INDEX"]
    )
    return audio, stream

def audioProcess(frames):
    audio_bytes = b"".join(frames)
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
    audio_np = audio_np.astype(np.float32) / 32768.0
    return audio_np

def createPrompt(audio_np, whisper_model):
    segments, _ = whisper_model.transcribe(audio_np)
    prompt = " ".join(s.text for s in segments)
    prompt = prompt.strip()

    return prompt

def createWakeWordModel():
    return Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")

def createWhisperModel(
    model_size: str = "base.en",
    device: Literal["cpu", "cuda"] = "cpu",
    compute_type: Literal["int8", "float16", "np.float32"] = "int8"
) -> WhisperModel:
    return WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type
    )