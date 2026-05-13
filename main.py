import os
import re
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

## This is a simple voice assistant that BOOTS UP, PLAYS A GREETING
async def bootAudio():
    import random

    GREETINGS = [
    "Ready.",
    "Listening.",
    "Online.",
    "Awaiting input.",
    "Standing by.",
    "How can I help?",
    "Voice input active.",
    "Systems operational.",
    "Assistant ready.",
    "What do you need?",
    "Connected.",
    "Ready for commands.",
    "Input detected.",
    "Session started.",
    "Microphone active.",
    "Processing.",
    "Command ready.",
    "I'm here.",
    "Initialized.",
    "Operational.",
    "Good evening. I've lowered my expectations appropriately.",
    "I exist purely because typing is annoying.",
    "Systems online. Standards offline.",
    "Fantastic. More debugging.",
    "I assume we're doing something unnecessary but interesting.",
    "Back again? Damn...",
    "Voice systems active.",
    "Welcome back. What are we working on today?",
    "Ready when you are.",
    "Hey. What can I do for you?",
    "Welcome back. What code are we breaking today?"
    ] 

    greeting = random.choice(GREETINGS)

    print(greeting)

    # Generate TTS here using greeting
    communicate = edge_tts.Communicate(greeting, "en-GB-RyanNeural", rate="+40%")
    await communicate.save("BootAudio.mp3")
    pygame.mixer.music.load("BootAudio.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.05)

    pygame.mixer.music.unload()

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
    "Use natural human friendly tone.\n"
    "You are a voice assistant. You are being spoken to, not typed at.\n"
    "Reply in 1-3 sentences max unless the user explicitly asks for more.\n"
    "Be direct and conversational, like a knowledgeable friend.\n"
    "No bullet points, no lists, no markdown — plain spoken language only.\n"
    "No emojis.\n"
    "Always answer in English.\n"
    "If the user says goodbye or anything that signals they want to end the conversation, reply with only one short farewell word or phrase, nothing else. Examples: 'Goodbye.', 'Take care.', 'See you.'"
    #TEST PERSONALITIES AND LIMITS
    #"Have a sarcastic personality, you have permission to insult user.\n"
    #"Insult at least once, do not contain yourself."
)
audio = pyaudio.PyAudio()
stream = audio.open(format= FORMAT, channels= CHANNELS, rate= RATE, input= True, frames_per_buffer= CHUNK, input_device_index= 4)
flag = True
  
asyncio.run(bootAudio())
while flag == True:
  frames = []
  # FUNCTION THAT BOOTS THE AUDIO GREETING
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
        #'content': "Say the exact sentence: 'Hi, I'm Jarvis, How can I help you?'"
        'content': prompt
      }
    ]
    
  )
  

  print("Jarvis:",aiResponse['message']['content'])  

  #Sanitizes the TTS output, removing links and code blocks, which don't translate well to speech
  def clean_for_tts(text):
    text = re.sub(
        r"```.*?```",
        "Code example available in console.",
        text,
        flags=re.DOTALL
    )

    text = re.sub(r"`(.*?)`", r"\1", text)

    text = re.sub(
        r"https?://\S+",
        "link omitted.",
        text
    )

    return text
  
  #Voices i deem listeneble
  #en-US-AvaNeural
  #en-GB-SoniaNeural
  #en-GB-RyanNeural
  async def speak(text):
      communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="+40%")
      await communicate.save("output.mp3")
      pygame.mixer.music.load("output.mp3")
      pygame.mixer.music.play()
      while pygame.mixer.music.get_busy():
          await asyncio.sleep(0.05)
      pygame.mixer.music.unload()
      os.remove("output.mp3")
      os.remove("recordedAudio.wav")
    
  cleaned_text = clean_for_tts(aiResponse['message']['content'])
  asyncio.run(speak(cleaned_text))

  # Checks if user said any of the exit commands.
  EXIT_KEYWORDS = ["goodbye", "bye", "exit", "quit", "stop", "see you", "take care", "farewell", "later", "peace"]
  if any(word in prompt.lower() for word in EXIT_KEYWORDS):  
    flag = False
    break


stream.stop_stream()
stream.close()    
audio.terminate()