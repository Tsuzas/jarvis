import os
import re
import time
import wave
import pygame
import pyaudio
import asyncio
import edge_tts
import webrtcvad
import numpy as np
import openwakeword
from openwakeword.model import Model
from ollama import chat
from faster_whisper import WhisperModel

# Download models on first run 
openwakeword.utils.download_models()

# VAD aggressiveness 0-3
vad = webrtcvad.Vad(2)
CHUNK = 480

async def bootAudio():
    import random
    GREETINGS = [
        "Ready.", "Listening.", "Online.", "Awaiting input.", "Standing by.",
        "How can I help?", "Voice input active.", "Systems operational.",
        "Assistant ready.", "What do you need?", "Connected.",
        "Ready for commands.", "Input detected.", "Session started.",
        "Microphone active.", "Processing.", "Command ready.", "I'm here.",
        "Initialized.", "Operational.",
        "Good evening. I've lowered my expectations appropriately.",
        "I exist purely because typing is annoying.",
        "Systems online. Standards offline.", "Fantastic. More debugging.",
        "I assume we're doing something unnecessary but interesting.",
        "Back again? Damn...", "Voice systems active.",
        "Welcome back. What are we working on today?", "Ready when you are.",
        "Hey. What can I do for you?", "Welcome back. What code are we breaking today?"
    ]
    greeting = random.choice(GREETINGS)
    print(greeting)
    communicate = edge_tts.Communicate(greeting, "en-GB-RyanNeural", rate="+40%")
    await communicate.save("BootAudio.mp3")
    pygame.mixer.music.load("BootAudio.mp3")
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
    await communicate.save("output.mp3")
    pygame.mixer.music.load("output.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.05)
    pygame.mixer.music.unload()
    os.remove("output.mp3")

def is_loud_enough(frame, threshold=1000):
    audio = np.frombuffer(frame, dtype=np.int16)
    return np.abs(audio).mean() > threshold

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

STATE = "WAKE"
OUTPUT_FILENAME = "recordedAudio.wav"
APPS = {
    "brave": r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Brave.lnk",
    "code": r"C:\Users\fpere\Desktop\Code - Shortcut.lnk",
    "steam": r"C:\Users\fpere\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Steam\Steam.lnk"
}
EXIT_KEYWORDS = ["goodbye", "bye", "exit", "quit", "stop", "see you", "take care", "farewell", "later", "peace", "close"]
TERMINATE_kEYWORDS =["","",""]
SYSTEM_PROMPT = (
    "You are a fast conversational assistant.\n"
    "Use natural human friendly tone.\n"
    "You are a voice assistant. You are being spoken to, not typed at.\n"
    "Reply in 1-3 sentences max unless the user explicitly asks for more.\n"
    "Be direct and conversational, like a knowledgeable friend.\n"
    "No bullet points, no lists, no markdown — plain spoken language only.\n"
    "No emojis.\n"
    "Always answer in English.\n"
    "If the user says goodbye or anything that signals they want to end the conversation, reply with only one short farewell word or phrase, nothing else. Examples: 'Goodbye.', 'Take care.', 'See you.'"
    "If User ask to open something, simply answer:'Opening (thing)...' "
)

## OPENWAKEWORD + PYAUDIO + WHISPER SETUP
oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

audio = pyaudio.PyAudio()
stream = audio.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=1280,
    input_device_index=4
)

asyncio.run(bootAudio())
print("Listening for 'Hey Jarvis'...")

try:
    while True:

        if STATE == "WAKE":
            raw = stream.read(320, exception_on_overflow=False)
            pcm = np.frombuffer(raw, dtype=np.int16)
            prediction = oww_model.predict(pcm)
            time.sleep(0.02) 
            if prediction["hey_jarvis"] > 0.5:
                print("Hey Jarvis detected!")
                oww_model.reset()

                STATE = "LISTEN"
                asyncio.run(bootAudio())


        elif STATE == "LISTEN":
            frames = record_until_silence(stream)

            if not frames or len(frames) < 15:
                print("Ignored audio")
                STATE = "LISTEN"
                continue

            audio_bytes = b"".join(frames)

            wf = wave.open(OUTPUT_FILENAME, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(audio_bytes)
            wf.close()

            STATE = "PROCESS"


        elif STATE == "PROCESS":
            segments, _ = whisper_model.transcribe(OUTPUT_FILENAME)
            prompt = " ".join(s.text for s in segments)
            prompt = prompt.strip()

            if not prompt:
                print("Empty transcription ignored")
                STATE = "LISTEN"
                continue
            print("\nYou said:", prompt)
            
            aiResponse = chat(
                model='mistral:7b',
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': prompt}
                ]
            )

            response_text = aiResponse['message']['content']
            print("Jarvis:", response_text)

            cleaned_text = clean_for_tts(response_text)
            asyncio.run(speak(cleaned_text))
            STATE = "LISTEN"

            if any(word in prompt.lower() for word in EXIT_KEYWORDS):
                print("Returning to wake word detection...")
                STATE = "WAKE"

            #if any(word in prompt.lower() for word in OPEN_WORDS):
            #        print(f"Opening {word}...")
            #        os.startfile(f"{word}.exe")
            #        STATE = "WAKE"
            for app in APPS:
                if app in prompt.lower():
                    print(f"Opening {app}...")
                    os.startfile(APPS[app])
                    STATE = "WAKE"
                    break
        else:
            STATE = "WAKE"

finally:
    stream.stop_stream()
    stream.close()
    audio.terminate()