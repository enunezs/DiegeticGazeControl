# voice_integration.py
# Continuous listening voice assistant (Ubuntu + Docker compatible)

import json
import time
import csv
import os
from datetime import datetime

import sounddevice as sd
import pyttsx3 #Replaces windows tts becuase it will not work on ubuntu
from vosk import Model, KaldiRecognizer #using vosk 50mb package (smaller)


# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models/vosk-model-small-en-us-0.15") #vosk model to be put in models folder

SAMPLE_RATE = 16000
LISTEN_SECONDS = 4
WAKE_WORD = "robot"
COOLDOWN_SEC = 2

LOG_FILE = "assistant_log.csv"

COMMANDS = {
    "open": "Opening gripper",
    "close": "Closing gripper",
    "home": "Moving to home position",
    "status": "System is online and ready",
    "help": "Say robot open, robot close, robot home, or robot stop",
    "stop": "Emergency stop activated"

    #TASK MAP:
    #"move forward": "MOVE_FORWARD",
    #"move backward": "MOVE_BACKWARD",
    #"turn left": "TURN_LEFT",
    #"turn right": "TURN_RIGHT",
    #"stop": "STOP",
    #"medicine": "GRAB_MEDICINE",
    #"cup": "PICK_UP_CUP",
    #"glassess": "PICK_UP_GLASSES",
    #"home": "RETURN_HOME",
    #"handover": "HANDOVER_OBJECT"
}


# pyttsx3 for Linux (this would not be able to run properly on windows)
engine = pyttsx3.init()
engine.setProperty("rate", 160)

def speak(text: str):
    print("Robot:", text)
    engine.say(text)
    engine.runAndWait()


# LOGGING
def init_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "heard", "command", "executed"])


def log_event(heard, cmd, executed):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            heard,
            cmd if cmd else "",
            executed
        ])


# SPEECH RECOGNITION
print("Loading Vosk model...")
model = Model(MODEL_PATH)
print("Model loaded.")

def recognise_once():
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    print("\nListening...")
    audio = sd.rec(int(LISTEN_SECONDS * SAMPLE_RATE),
                   samplerate=SAMPLE_RATE,
                   channels=1,
                   dtype="int16",
                   device=7) # Set to microphone device index 
    sd.wait()

    rec.AcceptWaveform(audio.tobytes())
    result = json.loads(rec.Result())

    return result.get("text", "").lower().strip()


def extract_command(text):
    if "stop" in text:
        return "stop"

    for cmd in COMMANDS:
        if cmd in text:
            return cmd

    return None

# MAIN
def main():
    init_log()

    speak("Voice system ready")

    last_exec_time = 0

    while True:
        text = recognise_once()

        if not text:
            continue

        print("Heard:", text)

        # Emergency override always active (for safety)
        if "stop" in text:
            speak(COMMANDS["stop"])
            log_event(text, "stop", True)
            last_exec_time = time.time()
            continue

        # Require wake word
        if WAKE_WORD not in text:
            continue

        cmd = extract_command(text)

        if not cmd:
            speak("Command not recognised")
            log_event(text, None, False)
            continue

        # Cooldown protection
        if time.time() - last_exec_time < COOLDOWN_SEC:
            speak("Please wait")
            continue

        speak(COMMANDS[cmd])
        log_event(text, cmd, True)
        last_exec_time = time.time()


if __name__ == "__main__":
    main()

