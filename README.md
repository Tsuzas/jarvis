# Jarvis

Local voice assistant — speak to it, it speaks back.

## Stack
- **WAKE** - Wakeupword: OpenWakeWord
- **STT** - faster-whisper (base, CPU int8)
- **LLM** - Mistral 7B via Ollama
- **TTS** - edge-tts (en-US-GuyNeural)

## Setup
```bash
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
## Setup Ubuntu ## Still in progress
``` bash
Install python3.11-venv
python3.11 -m venv venv
source venv/bin/activate
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
- You can interrupt the ai by pressing "ESC" to skip the TTS prompt and allowing you to speak again
- Microphone input is disabled during TTS playback to avoid feedback loops

# Jarvis Voice Assistant
Wake word activated voice assistant built with Python.

## Stack
- Wake word: OpenWakeWord
- STT: faster-whisper
- LLM: Mistral 7b via Ollama
- TTS: Edge TTS

## Setup
pip install -r requirements.txt
...

## Short & Long term vision

- privatization of hardcoded paths and AI configs
- Merge intent with system prompt or make the prompt good enough to Parse and talk with user
- Separate everything since its starting to be a bit cluttered
- Parallel actions so i can reenable AI without pressing ESC
- Possibly allow manual selection of which microphone to use instead of index
- Move on from tkinter to a more solid UI
- Optimize flow with the goal of User to text to ai to TTs to user to be seamless

## Known Bugs

### Multi-action intent execution
- Due to intention prompt, bad structuring of intent, action and by not handling arrays properly, we cannot open multiple apps at the same time as in previous versions. Will work on in the future.

### Tkinter threading instability
- Some illegal coding in the creation of tkinter causing erros in threading. This occurs because Tkinter is being accessed outside the main thread. Its holding on by a ... thread, will be fixed when refactor into ui.py or another UI library