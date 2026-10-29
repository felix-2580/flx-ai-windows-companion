"""FLX.AI Windows Companion v3: allow-listed local Windows actions only."""
import os, re, subprocess, threading, time, webbrowser
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

APP=Flask(__name__)
CORS(APP, resources={r"/*":{"origins":["https://flx-ai-demo.onrender.com","http://127.0.0.1:5000","http://localhost:5000","null"]}}, methods=["GET","POST","OPTIONS"], allow_headers=["Content-Type"])
def reply(message,category="success"): return jsonify({"message":message,"category":category})
def norm(s): return re.sub(r"\s+"," ",re.sub(r"[^\w\s.%:-]"," ",(s or "").lower())).strip()
def launch(target,label):
    try:
        if target.startswith("URI:"): os.startfile(target[4:])
        elif target.startswith("SHELL:"): os.startfile(target[6:])
        elif target.startswith("ms-") or target.endswith(":"): os.startfile(target)
        elif target.startswith("EXPLORER:"): subprocess.Popen(["explorer.exe",target[9:]],shell=False)
        elif target.startswith("MMC:"): subprocess.Popen(["mmc.exe",target[4:]],shell=False)
        else: subprocess.Popen([target],shell=False)
        return f"Opening {label}.","success"
    except Exception as e: return f"Couldn't open {label}. It may not be installed or registered on this PC.","error"
APP_TARGETS={
"file explorer":("EXPLORER:","File Explorer"),"explorer":("EXPLORER:","File Explorer"),"notepad":("notepad.exe","Notepad"),"calculator":("calc.exe","Calculator"),"calc":("calc.exe","Calculator"),"paint":("mspaint.exe","Paint"),"snipping tool":("ms-screenclip:","Snipping Tool"),"clock":("ms-clock:","Clock"),"settings":("ms-settings:","Windows Settings"),"task manager":("taskmgr.exe","Task Manager"),"control panel":("SHELL:shell:ControlPanelFolder","Control Panel"),"terminal":("wt.exe","Windows Terminal"),"windows terminal":("wt.exe","Windows Terminal"),"command prompt":("cmd.exe","Command Prompt"),"powershell":("powershell.exe","PowerShell"),"photos":("ms-photos:","Photos"),"media player":("mswindowsmusic:","Media Player"),"word":("winword.exe","Microsoft Word"),"microsoft word":("winword.exe","Microsoft Word"),"excel":("excel.exe","Microsoft Excel"),"microsoft excel":("excel.exe","Microsoft Excel"),"powerpoint":("powerpnt.exe","Microsoft PowerPoint"),"power point":("powerpnt.exe","Microsoft PowerPoint"),"microsoft powerpoint":("powerpnt.exe","Microsoft PowerPoint"),"device manager":("MMC:devmgmt.msc","Device Manager"),"resource monitor":("resmon.exe","Resource Monitor"),"services":("MMC:services.msc","Services"),"registry editor":("regedit.exe","Registry Editor"),"event viewer":("MMC:eventvwr.msc","Event Viewer"),"system information":("msinfo32.exe","System Information"),"character map":("charmap.exe","Character Map"),"magnifier":("magnify.exe","Magnifier"),"on screen keyboard":("osk.exe","On-Screen Keyboard"),"edge":("msedge.exe","Microsoft Edge"),"microsoft edge":("msedge.exe","Microsoft Edge"),"chrome":("chrome.exe","Google Chrome"),"google chrome":("chrome.exe","Google Chrome"),"firefox":("firefox.exe","Firefox"),"spotify":("spotify:","Spotify"),"whatsapp":("whatsapp:","WhatsApp"),"vscode":("code","Visual Studio Code"),"visual studio code":("code","Visual Studio Code"),"bluetooth settings":("ms-settings:bluetooth","Bluetooth settings"),"wifi settings":("ms-settings:network-wifi","Wi-Fi settings"),"wi fi settings":("ms-settings:network-wifi","Wi-Fi settings"),"display settings":("ms-settings:display","Display settings"),"sound settings":("ms-settings:sound","Sound settings"),"windows update":("ms-settings:windowsupdate","Windows Update"),"personalization settings":("ms-settings:personalization","Personalization settings"),"apps settings":("ms-settings:appsfeatures","Installed apps settings"),"storage settings":("ms-settings:storagesense","Storage settings"),"network settings":("ms-settings:network-status","Network settings")}
def folder_target(name):
    h=Path.home(); folders={"downloads":h/"Downloads","download":h/"Downloads","desktop":h/"Desktop","documents":h/"Documents","document":h/"Documents","pictures":h/"Pictures","photos":h/"Pictures","music":h/"Music","videos":h/"Videos","home":h,"user folder":h,"this pc":None,"computer":None,"recycle bin":"SHELL:shell:RecycleBinFolder","network":"SHELL:shell:NetworkPlacesFolder"}
    t=folders.get(name,"NOT_FOUND")
    if t=="NOT_FOUND": return None
    if t is None: return launch("EXPLORER:","This PC")
    if isinstance(t,Path):
        if not t.exists(): return f"I couldn't find the {name} folder.","error"
        try: os.startfile(str(t)); return f"Opening {name.title()}.","success"
        except Exception: return f"Couldn't open {name}.","error"
    return launch(t,name.title())
def volume(c):
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        dev=AudioUtilities.GetSpeakers(); iface=dev.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None); vol=cast(iface,POINTER(IAudioEndpointVolume))
        if "mute" in c or "unmute" in c:
            mute=("mute" in c and "unmute" not in c);vol.SetMute(1 if mute else 0,None);return ("System audio muted." if mute else "System audio unmuted."),"success"
        m=re.search(r"(\d{1,3})\s*(?:%|percent)",c);p=int(m.group(1)) if m else round(vol.GetMasterVolumeLevelScalar()*100)+(10 if any(x in c for x in ("increase","up","louder","raise")) else -10);p=max(0,min(100,p));vol.SetMasterVolumeLevelScalar(p/100,None);return f"System volume set to {p}%.","success"
    except Exception: return "Volume control failed. Check that pycaw and comtypes are installed.","error"
def brightness(c):
    try:
        import screen_brightness_control as sbc
        cur=sbc.get_brightness(display=0);cur=cur[0] if isinstance(cur,list) else cur;m=re.search(r"(\d{1,3})\s*(?:%|percent)",c);p=int(m.group(1)) if m else int(cur)+(10 if any(x in c for x in ("increase","up","brighter","raise")) else -10);p=max(0,min(100,p));sbc.set_brightness(p,display=0);return f"Screen brightness set to {p}%.","success"
    except Exception: return "Brightness control is unsupported on this display or driver.","error"
def wifi(c):
    # Fixed PowerShell script; user text is never inserted into a shell command.
    action="Enable-NetAdapter" if any(x in c for x in (" on","enable","turn wifi on","turn wi fi on")) else "Disable-NetAdapter"
    script=f"$a=Get-NetAdapter | Where-Object {{$_.Name -match 'Wi-Fi|WiFi|Wireless' -or $_.InterfaceDescription -match 'Wireless|Wi-Fi'}} | Select-Object -First 1; if($null -eq $a){{Write-Output 'NO_ADAPTER'; exit 3}}; {action} -Name $a.Name -Confirm:$false -ErrorAction Stop; Write-Output 'OK'"
    try:
        r=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",script],capture_output=True,text=True,timeout=15)
        if r.returncode==0:return ("Wi-Fi adapter enabled." if action=="Enable-NetAdapter" else "Wi-Fi adapter disabled."),"success"
        if "NO_ADAPTER" in (r.stdout+r.stderr):return "Couldn't find a Wi-Fi adapter. You can open Wi-Fi settings instead.","error"
        return "Windows couldn't change the Wi-Fi adapter. Try running the companion with suitable permissions, or use Wi-Fi settings.","error"
    except Exception:return "Wi-Fi control failed. Try opening Wi-Fi settings.","error"
def handle(raw):
    c=norm(raw)
    if not c:return "Please type or speak a command.","error"
    fm=re.search(r"\b(?:open|show|go to|browse to)\s+(?:my\s+)?(downloads?|desktop|documents?|pictures|photos|music|videos|home|user folder|this pc|computer|recycle bin|network)\b",c)
    if fm:
        n=fm.group(1);n={"download":"downloads","document":"documents","computer":"this pc"}.get(n,n);r=folder_target(n)
        if r:return r
    for alias in sorted(APP_TARGETS,key=len,reverse=True):
        if re.search(rf"\b(?:open|launch|start|run)\s+(?:the\s+)?{re.escape(alias)}\b",c):return launch(*APP_TARGETS[alias])
    if "volume" in c or c in ("mute","unmute","louder","quieter"):
        if any(x in c for x in ("increase","decrease","up","down","louder","quieter","set","mute","unmute","raise","lower")):return volume(c)
    if "brightness" in c or c in ("brighter","dimmer"):
        if any(x in c for x in ("increase","decrease","up","down","brighter","dimmer","set","raise","lower")):return brightness(c)
    if "wifi" in c or "wi-fi" in c or "wi fi" in c:
        if any(x in c for x in ("on","off","enable","disable","turn","activate")):return wifi(c)
        return launch("URI:ms-settings:network-wifi","Wi-Fi settings")
    if "bluetooth" in c:
        if any(x in c for x in ("on","off","enable","disable","turn")):return launch("URI:ms-settings:bluetooth","Bluetooth settings; use the Windows toggle to confirm the change")
        return launch("URI:ms-settings:bluetooth","Bluetooth settings")
    try:
        import pyautogui
        if any(x in c for x in ("switch window","next window","change window","alt tab")):pyautogui.hotkey("alt","tab");return "Switched to the next window.","success"
        if any(x in c for x in ("show desktop","minimize all windows")):pyautogui.hotkey("win","d");return "Showing the desktop.","success"
        if "minimize window" in c:pyautogui.hotkey("win","down");return "Minimize shortcut sent.","success"
        if "maximize window" in c:pyautogui.hotkey("win","up");return "Maximize shortcut sent.","success"
        if any(x in c for x in ("pause music","play music","play pause","toggle media")):pyautogui.press("playpause");return "Media play/pause shortcut sent.","success"
        if "next track" in c:pyautogui.press("nexttrack");return "Next-track shortcut sent.","success"
        if "previous track" in c:pyautogui.press("prevtrack");return "Previous-track shortcut sent.","success"
        if "take screenshot" in c or "screenshot" in c:
            import pyautogui
            p=Path.home()/"Pictures"/"FLXAI-screenshot.png";pyautogui.screenshot().save(str(p));return f"Screenshot saved to {p}.","success"
    except Exception:return "That Windows shortcut failed. Check companion permissions and dependencies.","error"
    if c in ("help","commands","what can you do","show commands"):
        return "Try: open Calculator, Notepad, Chrome, Word, Excel, PowerPoint, Task Manager, Device Manager, Downloads, Documents, Wi-Fi settings, Bluetooth settings, increase volume, set volume to 40 percent, increase brightness, show desktop, pause music, or take screenshot.","success"
    return "I don't recognise that Windows command. Type 'help' for examples. Apps must be installed, and some controls depend on Windows permissions or hardware.","error"
@APP.get("/health")
def health():return jsonify({"ok":True,"app":"FLX.AI Windows Companion","version":"3.0"})
@APP.route("/command",methods=["POST","OPTIONS"])
def command_route():
    if request.method=="OPTIONS":return "",204
    d=request.get_json(silent=True) or {};m,c=handle(str(d.get("command","")));return reply(m,c),(200 if c=="success" else 400)
def open_page():time.sleep(1.2);webbrowser.open("https://flx-ai-demo.onrender.com")
if __name__=="__main__":
    print("FLX.AI Windows Companion v3 running. Health: http://127.0.0.1:8765/health")
    threading.Thread(target=open_page,daemon=True).start();APP.run(host="127.0.0.1",port=8765,debug=False,threaded=True)
