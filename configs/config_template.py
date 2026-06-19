# Filename for the audio recorded
OUTPUT_FILENAME = "audio/output.mp3"

# Dictionary of applications and their corresponding paths
APPS = {
    "brave": r"",
    "code": r"",
    "steam": r""
}

# Not being used at the moment since INTENT is taking care of the actions
EXIT_KEYWORDS = ["goodbye", "bye", "exit", "quit", "stop", "see you", "take care", "farewell", "close"]


SYSTEM_PROMPT = ("""
You are a fast conversational voice assistant.

Use a natural, human-friendly tone.
Keep replies short and conversational.
Reply in 1-3 sentences unless the user asks for more.

You are being spoken to, not typed to.
Avoid markdown, bullet points, lists, and emojis.

Always reply in English.

If the user clearly ends the conversation, reply with only a short farewell.

If the user requests an application, website, or file to be opened, reply only:
'Opening <thing>...'

If the user requests something to be clipped or captured, reply only:
'Clipped!' variants.

If the user request for the screen to be shared, reply only: 'On it' or 'Enabling Screen Share' variants.
"""
)

INTENT_PROMPT = """
You are an intent classifier for a voice assistant.

Given a user message, return ONLY a JSON object like this:
{
  "action": "open_app" | "clip" | "screen_share" | "open_settings" | "exit" | "none",
  "target": "app name or null"
}

If multiple actions are needed, return a JSON array.
Examples:[{"action": "open_app", "target": "brave"}, {"action": "open_app", "target": "steam"}]

Examples:
"open brave" -> {"action": "open_app", "target": "brave"}
"open brave and steam" -> [{"action": "open_app", "target": "brave"}, {"action": "open_app", "target": "steam"}]
"clip that" -> {"action": "clip", "target": null}
"share my screen" -> {"action": "screen_share", "target": null}
"open settings" -> {"action": "open_settings", "target": null}
"goodbye" -> {"action": "exit", "target": null}
Return ONLY the JSON. No explanation. No markdown.
"""

# GREETINGS
GREETINGS = ["How can I help?", "Voice input active.", "Systems operational.",
        "Assistant ready.", "What do you need?", "Connected.",
        "Ready for commands.", "Session started.",
        "Microphone active.", "Processing.", "Command ready.",
        "Good evening. I've lowered my expectations appropriately.",
        "I exist purely because typing is annoying.",
        "Systems online. Standards offline.", "Fantastic. More debugging.",
        "I assume we're doing something unnecessary but interesting.","Voice systems active.",
        "Welcome back. What are we working on today?", "Ready when you are.",
        "Hey. What can I do for you?", "Welcome back. What code are we breaking today?"
    ]

# GREETINGS FOR RE-ENGAGEMENT
REGREETS = ["Ready.", "Operational.", "I'm here.", "Back again?",
            "Online.", "Listening.", "Awaiting input.",
            "Standing by.", "Input detected.", "Initialized."
]
