"""FLX.AI Windows Companion: loopback-only, allow-listed Windows controls."""
import os
import re
import subprocess
import sys
import threading
import time
import webbrowser

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
ALLOWED_ORIGINS = [
    "https://flx-ai-demo.onrender.com",
    "http://127.0.0.1",
    "http://localhost",
    "null",  # optional local-file preview
]
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}}, methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])

APP_ALIASES = {
    "notepad": ("notepad.exe", "Notepad"),
    "calculator": ("calc.exe", "Calculator"),
    "calc": ("calc.exe", "Calculator"),
    "paint": ("mspaint.exe", "Paint"),
    "file explorer": ("explorer.exe", "File Explorer"),
    "explorer": ("explorer.exe", "File Explorer"),
    "task manager": ("taskmgr.exe", "Task Manager"),
    "settings": ("ms-settings:", "Windows Settings"),
    "command prompt": ("cmd.exe", "Command Prompt"),
    "wordpad": ("write.exe", "WordPad (if installed)"),
}


def result(message, category="success"):
    return jsonify({"message": message, "category": category})


def set_volume(percent=None, delta=None, mute=False):
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        device = AudioUtilities.GetSpeakers()
        interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        if mute:
            current = bool(volume.GetMute())
            volume.SetMute(0 if current else 1, None)
            return "System audio muted." if not current else "System audio unmuted."
        if percent is not None:
            p = max(0, min(100, percent))
            volume.SetMasterVolumeLevelScalar(p / 100.0, None)
            return f"System volume set to {p}%."
        current = volume.GetMasterVolumeLevelScalar() * 100
        p = max(0, min(100, round(current + delta)))
        volume.SetMasterVolumeLevelScalar(p / 100.0, None)
        return f"System volume set to {p}%."
    except Exception as exc:
        return f"Couldn't control system volume: {exc}"


def set_brightness(percent=None, delta=None):
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness(display=0)
        if isinstance(current, list):
            current = current[0]
        p = max(0, min(100, percent if percent is not None else int(current) + delta))
        sbc.set_brightness(p, display=0)
        return f"Screen brightness set to {p}%."
    except Exception as exc:
        return f"Couldn't control brightness on this display: {exc}"


def launch_app(alias):
    target, display = APP_ALIASES[alias]
    try:
        if target == "ms-settings:":
            os.startfile(target)
        else:
            subprocess.Popen([target], shell=False)
        return f"Opening {display}."
    except Exception as exc:
        return f"Couldn't open {display}: {exc}"


def handle_command(raw):
    command = re.sub(r"\s+", " ", (raw or "").strip().lower())
    if not command:
        return "Please say or type a command.", "error"

    # Launch only known, explicitly allow-listed apps; never pass user text to a shell.
    for phrase, alias in [
        ("file explorer", "file explorer"), ("explorer", "explorer"),
        ("task manager", "task manager"), ("command prompt", "command prompt"),
        ("calculator", "calculator"), ("calc", "calc"), ("notepad", "notepad"),
        ("paint", "paint"), ("wordpad", "wordpad"), ("settings", "settings"),
    ]:
        if re.search(rf"\b(open|launch|start)\s+(the\s+)?{re.escape(phrase)}\b", command):
            return launch_app(alias), "success"

    if "mute" in command and ("volume" in command or command == "mute"):
        msg = set_volume(mute=True)
        return msg, "success" if msg.startswith("System audio") else "error"
    match = re.search(r"(?:volume|sound|audio).{0,20}?(?:to\s*)?(\d{1,3})\s*(?:%|percent)", command)
    if match:
        msg = set_volume(percent=int(match.group(1)))
        return msg, "success" if msg.startswith("System volume") else "error"
    if any(x in command for x in ["increase volume", "volume up", "louder", "turn up the volume"]):
        msg = set_volume(delta=10)
        return msg, "success" if msg.startswith("System volume") else "error"
    if any(x in command for x in ["decrease volume", "volume down", "quieter", "turn down the volume"]):
        msg = set_volume(delta=-10)
        return msg, "success" if msg.startswith("System volume") else "error"
    if "brightness" in command:
        match = re.search(r"(\d{1,3})\s*(?:%|percent)", command)
        if match:
            msg = set_brightness(percent=int(match.group(1)))
        elif any(x in command for x in ["increase", "up", "brighter"]):
            msg = set_brightness(delta=10)
        elif any(x in command for x in ["decrease", "down", "dimmer", "lower"]):
            msg = set_brightness(delta=-10)
        else:
            return "Try 'increase brightness', 'decrease brightness', or 'set brightness to 50 percent'.", "error"
        return msg, "success" if msg.startswith("Screen brightness") else "error"

    try:
        import pyautogui
        if any(x in command for x in ["switch window", "next window", "change window"]):
            pyautogui.hotkey("alt", "tab")
            return "Switched to the next window.", "success"
        if "minimize all" in command or "show desktop" in command:
            pyautogui.hotkey("win", "d")
            return "Showing the desktop.", "success"
        if "minimize window" in command:
            pyautogui.hotkey("win", "down")
            return "Minimize command sent to the active window.", "success"
        if "maximize window" in command:
            pyautogui.hotkey("win", "up")
            return "Maximize command sent to the active window.", "success"
    except Exception as exc:
        return f"Window control failed: {exc}", "error"

    if command in ("help", "what can you do", "commands"):
        return ("Try: open Notepad, open Calculator, open Paint, open File Explorer, open Task Manager, "
                "increase/decrease volume, set volume to 50 percent, mute volume, increase brightness, "
                "switch window, minimize window, maximize window, or show desktop."), "success"
    return ("I don't have that Windows action enabled yet. Say 'help' to see supported commands. "
            "For safety, I only run a fixed list of approved actions."), "error"


@app.get("/health")
def health():
    return jsonify({"ok": True, "app": "FLX.AI Windows Companion", "version": "1.0"})


@app.route("/command", methods=["POST", "OPTIONS"])
def command_route():
    if request.method == "OPTIONS":
        return ("", 204)
    data = request.get_json(silent=True) or {}
    message, category = handle_command(str(data.get("command", "")))
    return result(message, category), (200 if category == "success" else 400)


def open_local_page():
    time.sleep(1.2)
    webbrowser.open("https://flx-ai-demo.onrender.com")


if __name__ == "__main__":
    print("\nFLX.AI Windows Companion is running on this PC.")
    print("Open https://flx-ai-demo.onrender.com and allow microphone access.")
    print("Only approved commands are enabled. Press Ctrl+C to stop.\n")
    threading.Thread(target=open_local_page, daemon=True).start()
    # Loopback only: this service is not exposed to the school network/internet.
    app.run(host="127.0.0.1", port=8765, debug=False, threaded=True)
