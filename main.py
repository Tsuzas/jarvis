import os
import re
import time
import wave
import numpy as np
import pygame
import pyaudio
import asyncio
import edge_tts
import keyboard
import openwakeword
from openwakeword.model import Model
from ollama import chat
from faster_whisper import WhisperModel

## Download models on first run
openwakeword.utils.download_models()

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

## SETUP
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
pygame.mixer.init()

OUTPUT_FILENAME = "recordedAudio.wav"
EXIT_KEYWORDS = ["goodbye", "bye", "exit", "quit", "stop", "see you", "take care", "farewell", "later", "peace", "close"]
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
)

## OPENWAKEWORD + PYAUDIO SETUP
oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
model = WhisperModel("base", device="cpu", compute_type="int8")
  
audio = pyaudio.PyAudio()
stream = audio.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,  # openwakeword requires 16000
    input=True,
    frames_per_buffer=1280,
    input_device_index=4
)

asyncio.run(bootAudio())
print("Listening for 'Hey Jarvis'...")

try:
    while True:
        # WAKE WORD LOOP
        raw = stream.read(1280, exception_on_overflow=False)
        pcm = np.frombuffer(raw, dtype=np.int16)
        prediction = oww_model.predict(pcm)

        if prediction["hey_jarvis"] > 0.5:
            print("Hey Jarvis detected!")
            asyncio.run(bootAudio())

            # CONVERSATION LOOP
            while True:
                frames = []
                print("Press SPACE to start recording")
                keyboard.wait('space')
                print("Recording... Press SPACE to stop.")
                time.sleep(0.2)

                while True:
                    try:
                        data = stream.read(1280, exception_on_overflow=False)
                        frames.append(data)
                    except OSError:
                        pass
                    if keyboard.is_pressed('space'):
                        print("Stopping recording.")
                        time.sleep(0.2)
                        break

                wf = wave.open(OUTPUT_FILENAME, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(b''.join(frames))
                wf.close()

                
                segments, _ = model.transcribe(OUTPUT_FILENAME)
                prompt = " ".join(s.text for s in segments)
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

                if any(word in prompt.lower() for word in EXIT_KEYWORDS):
                    print("\n------------------------\nReturning to wake word detection...\n------------------------")
                    break  # back to wake word loop, not full exit

finally:
    stream.stop_stream()
    stream.close()
    audio.terminate()