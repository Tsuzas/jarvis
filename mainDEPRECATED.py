import os
import time
import wave
import pyttsx3
import asyncio
import pyaudio
import whisper
import edge_tts
import keyboard
from ollama import chat
import pygame

## SETS THE FFMPEG PATH
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"

pygame.mixer.init()
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
OUTPUT_FILENAME = "recordedAudio.wav"
SYSTEM_PROMPT = (
    "You are a fast conversational assistant.\n"
    "Keep replies short.\n"
    "Match user message length when possible.\n"
    "Use natural human friendly tone.\n"
    "No long explanations unless asked.\n"
    "Do not use emojis.\n"
    "If the word is unclear or possibly wrong, ask clarification instead of guessing.\n"
    "Do not assume recipes or technical steps if unsure.\n"
    "Answer in english"
)
audio = pyaudio.PyAudio()
stream = audio.open(format= FORMAT, channels= CHANNELS, rate= RATE, input= True, frames_per_buffer= CHUNK, input_device_index= 4)

frames = []
print("Press SPACE to start recording")  
keyboard.wait('space')
print("Recording... Press SPACE to stop.")
time.sleep(0.2)

while True:
    try:
        data = stream.read(CHUNK)  
        frames.append(data)
    except KeyboardInterrupt:
        break
    if keyboard.is_pressed('space'):
        print("stopping recording") 
        time.sleep(0.2)
        break   
      
stream.stop_stream()
stream.close()
audio.terminate()

wf = wave.open(OUTPUT_FILENAME, 'wb')  
wf.setnchannels(CHANNELS)
wf.setsampwidth(audio.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

model = whisper.load_model("tiny")
result = model.transcribe(OUTPUT_FILENAME)
print("PROMPT FROM AUDIO:",result["text"])

#gemma3:1b - SUPER FAST, BUT COMPLETELY WRONG IF REQUIRES THINKING
#qwen3.6:latest - SUPER SLOW BUT DETAILED
#mistral:7b - best inbetween honestly looks cool
aiResponse = chat(
  model='mistral:7b',
  messages=[
    {
      'role': 'system',
      'content': SYSTEM_PROMPT
    },
    {
      'role': 'user',
      'content': result["text"]
    }
  ]
)
engine = pyttsx3.init()
print("Qwen:",aiResponse['message']['content'])


async def speak(text):
    file = "output.mp3"

    communicate = edge_tts.Communicate(text,
    "en-US-GuyNeural",
    rate="+20%")
    #en-AU-NatashaNeural
    await communicate.save(file)

    pygame.mixer.music.load(file)  
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.05)
    pygame.mixer.music.unload()  
    os.remove(file)
    os.remove(OUTPUT_FILENAME)

asyncio.run(speak(aiResponse['message']['content']))