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
Run `main.py`, press SPACE to start recording, press SPACE again to stop.
