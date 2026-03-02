#Continuos listening done here

import json
import time
import csv
from datetime import datetime
import subprocess
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# CONFIG
MODEL_PATH = "/models/vosk-model-small-en-us-0.15"
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
}


# WINDOWS TTS
def speak(text: str):
    print("Assistant:", text)

    safe = text.replace("'", "")
    ps_script = f"""
    Add-Type -AssemblyName System.Speech;
    (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}');
    """

    subprocess.run(
        ["powershell", "-Command", ps_script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


# LOGGING
def init_log():
    try:
        with open(LOG_FILE, "x", newline="") as f:
            csv.writer(f).writerow([
                "timestamp", "heard", "command", "executed"
            ])
    except FileExistsError:
        pass


def log_event(heard, cmd, executed):
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            datetime.now().isoformat(timespec="seconds"),
            heard,
            cmd if cmd else "",
            executed
        ])


# SPEECH RECOGNITION
model = Model(MODEL_PATH)

def recognise_once():
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    print("\nListening...")
    audio = sd.rec(int(LISTEN_SECONDS * SAMPLE_RATE),
                   samplerate=SAMPLE_RATE,
                   channels=1,
                   dtype="int16")
    sd.wait()

    rec.AcceptWaveform(audio.tobytes())
    result = json.loads(rec.Result())
    return result.get("text","").lower().strip()


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

    speak("Voice assistant ready")

    last_exec_time = 0

    while True:
        text = recognise_once()
        if not text:
            continue

        print("Heard:", text)

        # emergency override always active
        if "stop" in text:
            speak(COMMANDS["stop"])
            log_event(text, "stop", True)
            last_exec_time = time.time()
            continue

        if WAKE_WORD not in text:
            continue

        cmd = extract_command(text)

        if not cmd:
            speak("Command not recognised")
            log_event(text, None, False)
            continue

        # cooldown protection
        if time.time() - last_exec_time < COOLDOWN_SEC:
            speak("Please wait")
            continue

        speak(COMMANDS[cmd])
        log_event(text, cmd, True)
        last_exec_time = time.time()


if __name__ == "__main__":
    main()

