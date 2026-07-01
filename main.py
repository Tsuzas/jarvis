"""
=========================================================
JARVIS VOICE ASSISTANT - PIPELINE OVERVIEW

This system is a real-time voice-driven state machine:

PIPELINE FLOW:
Audio Input → Wake Word Detection → Speech Capture →
Transcription → Intent Detection → Action Execution →
LLM Response → TTS Output → Return to Idle

STATE MACHINE:
WAKE    -> Listening for wake word ("Hey Jarvis")
LISTEN  -> Capturing user speech until silence
PROCESS -> Interpreting intent + generating response

Design philosophy:
- WAKE loop is CPU-light (continuous prediction)
- LISTEN is event-driven (silence-based recording)
- PROCESS is compute-heavy (AI + LLM + TTS)
=========================================================
"""

# IMPORTS necessary libraries
import time
import pygame
import asyncio
import numpy as np
import openwakeword

# Configuration layer (runtime settings, paths, UI assets)
import configs.configs as configs
config = configs.load_config()

# Audio subsystem (wake word, recording, processing, TTS)
import audio.audio as audio

# UI subsystem (overlay + system tray)
import gui.ui as ui

# AI subsystem (intent detection + LLM responses)
import ai.llm as llm


# Download models on first run (wake word models cached locally)
openwakeword.utils.download_models()

# GLOBAL STATE (shared runtime variables across pipeline stages)
global audio_np


# =========================
# SYSTEM INITIALIZATION
# =========================

# Initialize audio playback system (TTS + effects)
pygame.mixer.init()

# Async loop used for TTS and boot audio without blocking main thread
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# UI overlay shown when assistant is active (visual feedback layer)
overlay = ui.OverlayWindow(config["OVERLAY_GIF"])

# System tray icon (background presence / control)
ui.create_tray_icon()


# =========================
# STATE MACHINE INITIAL STATE
# =========================
STATE = "WAKE"


# =========================
# MODEL INITIALIZATION
# =========================

# Wake word detection model (low latency inference loop)
oww_model = audio.createWakeWordModel()

# Whisper model for speech-to-text transcription
whisper_model = audio.createWhisperModel()

# Audio input stream (microphone)
audios, stream = audio.openAudio()

# Boot audio greeting (first-run / startup feedback)
loop.run_until_complete(audio.bootAudio(first_boot=True))

print("Listening for 'Hey Jarvis'...")


# =========================
# MAIN LOOP (STATE MACHINE)
# =========================

try:
    while True:

        # =====================================================
        # WAKE STATE
        # Purpose: Detect wake word with minimal CPU usage
        # System stays idle until activation phrase is detected
        # =====================================================
        if STATE == "WAKE":

            # Read raw audio buffer from microphone stream
            # WHY: continuous stream required for real-time detection
            raw = stream.read(audio.CHUNK, exception_on_overflow=False)

            # Convert byte stream into PCM format for ML model
            pcm = np.frombuffer(raw, dtype=np.int16)

            # Wake word inference step
            prediction = oww_model.predict(pcm)

            # Small sleep reduces CPU usage while maintaining responsiveness
            time.sleep(0.02)

            # Trigger condition for wake word detection
            if prediction["hey_jarvis"] > 0.5:

                print("Hey Jarvis detected!")

                # Reset model state to avoid duplicate triggers
                oww_model.reset()

                # Show UI overlay (user feedback: system activated)
                overlay.show()

                # Transition: WAKE → LISTEN
                STATE = "LISTEN"

                # Play activation sound (non-blocking async call)
                loop.run_until_complete(audio.bootAudio(first_boot=False))


        # =====================================================
        # LISTEN STATE
        # Purpose: Capture user speech until silence is detected
        # =====================================================
        elif STATE == "LISTEN":

            # Play chime to indicate recording start
            audio.chimeSound()

            # Record audio until silence threshold is reached
            frames = audio.record_until_silence(stream)

            # Optional processing step to validate silence detection
            audio.silenceDetection(frames)

            # Convert recorded frames into numpy audio array
            audio_np = audio.audioProcess(frames)

            # Transition: LISTEN → PROCESS
            STATE = "PROCESS"


        # =====================================================
        # PROCESS STATE
        # Purpose: Convert speech → text → intent → action → response
        # =====================================================
        elif STATE == "PROCESS":

            # Speech-to-text transcription using Whisper
            prompt = audio.createPrompt(audio_np, whisper_model)

            # Validate transcription quality (filter noise / empty input)
            audio.checkTranscription(prompt)

            # -------------------------
            # FAST PATH: INTENT DETECTION
            # -------------------------
            # WHY: avoids unnecessary LLM calls for simple commands
            intentResponse = llm.get_intent(prompt)

            # Extract raw JSON-like string from model response
            raw = intentResponse.get("message", {}).get("content", "")

            print("Raw intent response:", raw)

            # Parse intent structure (action + target extraction)
            intent = llm.jsonify(raw)
            action, target = llm.separate_intent(intent)

            # Execute system action if valid intent detected
            llm.which_action_and_target(action, target)

            # -------------------------
            # LLM RESPONSE GENERATION
            # -------------------------
            # WHY: fallback / conversational response layer
            aiResponse = llm.get_answer(prompt)

            response_text = aiResponse['message']['content']
            print("Jarvis:", response_text)

            # Clean response for TTS (remove code blocks, links, noise)
            cleaned_text = audio.clean_for_tts(response_text)

            # Text-to-speech output (blocking async call)
            loop.run_until_complete(audio.speak(cleaned_text))

            # Hide overlay (system returns to idle state)
            overlay.hide()

            # Transition: PROCESS → WAKE
            STATE = "WAKE"


        # Fallback safety state (should never normally be reached)
        else:
            overlay.hide()


# =========================
# CLEAN SHUTDOWN HANDLER
# =========================
finally:
    stream.stop_stream()
    stream.close()
    audios.terminate()
    loop.close()