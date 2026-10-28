"""FLX.AI Windows Companion v2 - local, allow-listed Windows actions."""
import os
import re
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

APP = Flask(__name__)
WEBSITE_ORIGINS = [
    "https://flx-ai-demo.onrender.com",
    "http://127.0.0.1:5000",
    "http://localhost:5000",
    "null",
]
CORS(APP, resources={r"/*": {"origins": WEBSITE_ORIGINS}},
     methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])

def reply(message, category="success", **extra):
    return jsonify({"message": message, "category": category, **extra})

def normalize(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s.%:-]", " ", text)
    return re.sub(r"\s+", " ", text)

def known_folder(name):
    home = Path.home()
    folders = {
        "downloads": home / "Downloads",
        "download": home / "Downloads",
        "desktop": home / "Desktop",
        "documents": home / "Documents",
        "document": home / "Documents",
        "pictures": home / "Pictures",
        "photos": home / "Pictures",
        "music": home / "Music",
        "videos": home / "Videos",
        "home": home,
        "user folder": home,
        "this pc": None,
        "computer": None,
        "recycle bin": "shell:RecycleBinFolder",
        "control panel": "shell:ControlPanelFolder",
        "network": "shell:NetworkPlacesFolder",
    }
    return folders.get(name, "NOT_FOUND")

def open_target(target, display):
    try:
        if target.startswith("URI:"):
            os.startfile(target[4:])
        elif target.startswith("SHELL:"):
            os.startfile(target[6:])
        elif target.startswith("PATH:"):
            path = target[5:]
            if not os.path.exists(path):
                return f"I couldn't find {display} on this PC.", "error"
            os.startfile(path)
        elif target.startswith("EXPLORER:"):
            subprocess.Popen(["explorer.exe", target[9:]], shell=False)
        elif target.startswith("COMMAND:"):
            subprocess.Popen([target[8:]], shell=False)
        else:
            subprocess.Popen([target], shell=False)
        return f"Opening {display}.", "success"
    except Exception as exc:
        return f"Couldn't open {display}: {exc}", "error"

# Fixed allow-list. Unknown text is never passed to a shell.
APP_TARGETS = {
    "notepad": ("notepad.exe", "Notepad"),
    "calculator": ("calc.exe", "Calculator"),
    "calc": ("calc.exe", "Calculator"),
    "paint": ("mspaint.exe", "Paint"),
    "task manager": ("taskmgr.exe", "Task Manager"),
    "device manager": ("COMMAND:devmgmt.msc", "Device Manager"),
    "control panel": ("SHELL:shell:ControlPanelFolder", "Control Panel"),
    "file explorer": ("EXPLORER:", "File Explorer"),
    "explorer": ("EXPLORER:", "File Explorer"),
    "command prompt": ("cmd.exe", "Command Prompt"),
    "powershell": ("powershell.exe", "PowerShell"),
    "terminal": ("wt.exe", "Windows Terminal"),
    "snipping tool": ("ms-screenclip:", "Snipping Tool"),
    "on screen keyboard": ("osk.exe", "On-Screen Keyboard"),
    "magnifier": ("magnify.exe", "Magnifier"),
    "character map": ("charmap.exe", "Character Map"),
    "system information": ("msinfo32.exe", "System Information"),
    "resource monitor": ("resmon.exe", "Resource Monitor"),
    "services": ("services.msc", "Services"),
    "registry editor": ("regedit.exe", "Registry Editor"),
    "event viewer": ("eventvwr.msc", "Event Viewer"),
    "wordpad": ("write.exe", "WordPad (if installed)"),
    "edge": ("msedge.exe", "Microsoft Edge"),
    "microsoft edge": ("msedge.exe", "Microsoft Edge"),
    "chrome": ("chrome.exe", "Google Chrome"),
    "google chrome": ("chrome.exe", "Google Chrome"),
    "firefox": ("firefox.exe", "Firefox"),
    "vscode": ("code", "Visual Studio Code"),
    "visual studio code": ("code", "Visual Studio Code"),
    "spotify": ("spotify:", "Spotify"),
    "whatsapp": ("whatsapp:", "WhatsApp"),
    "settings": ("ms-settings:", "Windows Settings"),
    "bluetooth settings": ("ms-settings:bluetooth", "Bluetooth settings"),
    "wifi settings": ("ms-settings:network-wifi", "Wi-Fi settings"),
    "wi fi settings": ("ms-settings:network-wifi", "Wi-Fi settings"),
    "display settings": ("ms-settings:display", "Display settings"),
    "sound settings": ("ms-settings:sound", "Sound settings"),
    "windows update": ("ms-settings:windowsupdate", "Windows Update"),
    "personalization settings": ("ms-settings:personalization", "Personalization settings"),
    "apps settings": ("ms-settings:appsfeatures", "Installed apps settings"),
    "storage settings": ("ms-settings:storagesense", "Storage settings"),
    "network settings": ("ms-settings:network-status", "Network settings"),
}

def launch_app(name):
    target, display = APP_TARGETS[name]
    if target.startswith("ms-settings:") or target.endswith(":") or target.startswith("spotify:") or target.startswith("whatsapp:") or target.startswith("ms-screenclip:"):
        return open_target("URI:" + target, display)
    if target.startswith("COMMAND:"):
        # Known MMC snap-in only; no user-provided text is passed to a shell.
        try:
            subprocess.Popen(["mmc.exe", target[8:]], shell=False)
            return f"Opening {display}.", "success"
        except Exception as exc:
            return f"Couldn't open {display}: {exc}", "error"
    if target == "EXPLORER:":
        return open_target("EXPLORER:", display)
    return open_target(target, display)

def launch_folder(name):
    folder = known_folder(name)
    if folder == "NOT_FOUND":
        return None
    if folder is None:
        return open_target("EXPLORER:", "This PC")
    if isinstance(folder, Path):
        return open_target("PATH:" + str(folder), name.title())
    return open_target("SHELL:" + folder, name.title())

def volume_command(command):
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        device = AudioUtilities.GetSpeakers()
        interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        if "unmute" in command or "mute" in command:
            muted = bool(volume.GetMute())
            should_mute = "mute" in command and "unmute" not in command
            volume.SetMute(1 if should_mute else 0, None)
            return ("System audio muted." if should_mute else "System audio unmuted."), "success"
        match = re.search(r"(\d{1,3})\s*(?:%|percent)", command)
        if match:
            percent = max(0, min(100, int(match.group(1))))
        else:
            current = round(volume.GetMasterVolumeLevelScalar() * 100)
            delta = 10 if any(x in command for x in ("increase", "up", "louder", "raise")) else -10
            percent = max(0, min(100, current + delta))
        volume.SetMasterVolumeLevelScalar(percent / 100, None)
        return f"System volume set to {percent}%.", "success"
    except Exception as exc:
        return f"Couldn't control system volume: {exc}", "error"

def brightness_command(command):
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness(display=0)
        if isinstance(current, list):
            current = current[0]
        match = re.search(r"(\d{1,3})\s*(?:%|percent)", command)
        if match:
            percent = int(match.group(1))
        else:
            delta = 10 if any(x in command for x in ("increase", "up", "brighter", "raise")) else -10
            percent = int(current) + delta
        percent = max(0, min(100, percent))
        sbc.set_brightness(percent, display=0)
        return f"Screen brightness set to {percent}%.", "success"
    except Exception as exc:
        return f"Couldn't control brightness on this display: {exc}", "error"

def handle_command(raw):
    command = normalize(raw)
    if not command:
        return "Please say or type a command.", "error"

    # Folder intents first, so "open Downloads" isn't treated as an app.
    folder_match = re.search(r"\b(?:open|show|go to|browse to)\s+(?:my\s+)?(downloads?|desktop|documents?|pictures|photos|music|videos|home|user folder|this pc|computer|recycle bin|control panel|network)\b", command)
    if folder_match:
        folder_name = folder_match.group(1)
        if folder_name == "download": folder_name = "downloads"
        if folder_name == "document": folder_name = "documents"
        if folder_name == "computer": folder_name = "this pc"
        result = launch_folder(folder_name)
        if result:
            return result

    # Match longest app alias first to avoid matching a short alias too early.
    for alias in sorted(APP_TARGETS, key=len, reverse=True):
        if re.search(rf"\b(?:open|launch|start|run)\s+(?:the\s+)?{re.escape(alias)}\b", command):
            return launch_app(alias)

    if "volume" in command or "sound" in command or "audio" in command or command in ("mute", "unmute"):
        if any(x in command for x in ("increase", "decrease", "up", "down", "louder", "quieter", "set", "mute", "unmute", "raise", "lower")):
            return volume_command(command)
    if "brightness" in command:
        if any(x in command for x in ("increase", "decrease", "up", "down", "brighter", "dimmer", "set", "raise", "lower")):
            return brightness_command(command)
        return "Try 'increase brightness' or 'set brightness to 50 percent'.", "error"

    try:
        import pyautogui
        if any(x in command for x in ("switch window", "next window", "change window", "alt tab")):
            pyautogui.hotkey("alt", "tab")
            return "Switched to the next window.", "success"
        if any(x in command for x in ("show desktop", "minimize all windows")):
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

    if command in ("help", "commands", "what can you do", "show commands"):
        return ("Try: open Notepad, Calculator, Paint, Task Manager, Settings, Chrome, Edge, "
                "File Explorer, Downloads, Desktop, Documents, This PC, Device Manager, "
                "Wi-Fi settings, Sound settings, increase volume, set volume to 50 percent, "
                "increase brightness, switch window, minimize window, maximize window, or show desktop."), "success"

    return ("I don't recognize that command yet. Say 'help' for supported commands. "
            "App names must match an enabled command; some apps may not be installed on this PC."), "error"

@APP.get("/health")
def health():
    return jsonify({"ok": True, "app": "FLX.AI Windows Companion", "version": "2.0"})

@APP.route("/command", methods=["POST", "OPTIONS"])
def command_route():
    if request.method == "OPTIONS":
        return ("", 204)
    data = request.get_json(silent=True) or {}
    message, category = handle_command(str(data.get("command", "")))
    return reply(message, category), (200 if category == "success" else 400)

def open_local_page():
    time.sleep(1.2)
    webbrowser.open("https://flx-ai-demo.onrender.com")

if __name__ == "__main__":
    print("\nFLX.AI Windows Companion v2 is running on this PC.")
    print("Test status at http://127.0.0.1:8765/health")
    print("Open https://flx-ai-demo.onrender.com and allow local network access if prompted.")
    print("Press Ctrl+C to stop the companion.\n")
    threading.Thread(target=open_local_page, daemon=True).start()
    APP.run(host="127.0.0.1", port=8765, debug=False, threaded=True)
