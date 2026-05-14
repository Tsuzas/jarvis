# Jarvis

Local voice assistant — speak to it, it speaks back.

## Stack
- **STT** — faster-whisper (base, CPU int8)
- **LLM** — Mistral 7B via Ollama
- **TTS** — edge-tts (en-US-GuyNeural)

## Setup
```bash
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Requirements
- [Ollama](https://ollama.com) running locally with `mistral:7b` pulled
- [FFmpeg](https://ffmpeg.org) installed at `C:\ffmpeg\bin`
- Microphone set to device index 4 (adjust in code)

## Usage
Run `main.py`, Whenever you want to enable AI say, "Hey Jarvis", he'll answer, when a ring chimes, you can speak.

## Features
- Open applications (via configured paths or app mapping, I intend on using AI to further streamline this)
- Screen share trigger (keyboard shortcut automation)
- Clip/capture trigger (keyboard shortcut automation)
- Conversational voice responses via LLM

## Notes

- This is a continuous real-time voice loop system
- Input is processed sequentially (no parallel conversations)
- You cannot interrupt the assistant while it is speaking
- Microphone input is disabled during TTS playback to avoid feedback loops
