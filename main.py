import os
import time
import wave
import wave
import pygame
import pyaudio
import asyncio
import edge_tts
import keyboard
from ollama import chat
from faster_whisper import WhisperModel

## SETS THE FFMPEG PATH
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"

pygame.mixer.init()
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
OUTPUT_FILENAME = "recordedAudio.wav"
SYSTEM_PROMPT = (
    #"You are a fast conversational assistant.\n"
    #"Keep replies short.\n"
    #"Match user message length when possible.\n"
    #"Use natural human friendly tone.\n"
    #"No long explanations unless asked.\n"
    #"Do not use emojis.\n"
    #"If the word is unclear or possibly wrong, ask clarification instead of guessing.\n"
    #"Do not assume recipes or technical steps if unsure.\n"
    #"Answer in english"
    "You are a voice assistant. You are being spoken to, not typed at.\n"
    "Reply in 1-3 sentences max unless the user explicitly asks for more.\n"
    "Be direct and conversational, like a knowledgeable friend.\n"
    "No bullet points, no lists, no markdown — plain spoken language only.\n"
    "No emojis.\n"
    "Always answer in English."
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

model = WhisperModel("base", device="cpu", compute_type="int8")  
segments, _ = model.transcribe(OUTPUT_FILENAME)
prompt = " ".join(s.text for s in segments)  # forces the generator
print("\nYou said:", prompt)

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
      'content': prompt
    }
  ]
)
print("Jarvis:",aiResponse['message']['content'])  

#Voices i deem listeneble
#en-US-AvaNeural
#en-GB-SoniaNeural
#en-GB-RyanNeural
async def speak(text):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="+20%")
    await communicate.save("output.mp3")
    pygame.mixer.music.load("output.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.05)
    pygame.mixer.music.unload()
    os.remove("output.mp3")

asyncio.run(speak(aiResponse['message']['content']))