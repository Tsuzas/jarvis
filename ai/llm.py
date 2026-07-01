# IMPORT config and loads it
from configs.configs import load_config
config = load_config()

from ollama import chat
import json
import keyboard
import os
import gui.ui as ui


def get_intent(prompt):
    # second call - intent only
            intentResponse = chat(
                model= config["MODEL"],
                messages=[
                    {'role': 'system', 'content': config["INTENT_PROMPT"]},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return intentResponse

def separate_intent(intent):
    action = intent.get("action")
    target = intent.get("target")
    print("Intent detected:", action, "Target:", target)
    return action, target

def jsonify(raw):
    try:
        intent = json.loads(raw)
    except json.JSONDecodeError:
        print("Invalid model output:", raw)
        intent = {}
    return intent

def which_action_and_target(action, target):
    if action == "open_app" and target in config["APPS"]:
        print(f"Opening {target}...")
        os.startfile(config["APPS"][target])

    elif action == "clip":
        keyboard.send("left_alt + f10")

    elif action == "screen_share":
        keyboard.send('shift+l+p')

    elif action == "open_settings":
        ui.open_menu()

    elif action == "exit":
        print("Returning to wake word detection...")

def get_answer(prompt):
    aiResponse = chat(
            #DESKTOP mistral:7b
            model = config["MODEL"],
            messages=[
                {'role': 'system', 'content': config["SYSTEM_PROMPT"]},
                {'role': 'user', 'content': prompt}
            ]
            )
    return aiResponse