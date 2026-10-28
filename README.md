# FLX.AI Windows Companion v2

This local companion performs a fixed allow-list of Windows actions on the PC where it runs. It binds only to `127.0.0.1` and is not exposed to the school network.

## Supported examples
- Open Notepad, Calculator, Paint, Task Manager, Settings, Control Panel, Device Manager, Command Prompt, PowerShell, Terminal, Snipping Tool, System Information, Resource Monitor, Services, Event Viewer
- Open Chrome, Edge, Firefox, Visual Studio Code, Spotify or WhatsApp if installed and registered in Windows
- Open Downloads, Desktop, Documents, Pictures, Music, Videos, Home, This PC, Recycle Bin, Network
- Open Wi-Fi, Bluetooth, Display, Sound, Windows Update, Personalization and Installed Apps settings
- Volume, brightness and window shortcuts (device/driver support varies)

The app aliases are a fixed allow-list. Arbitrary dictated text is never passed to a shell.

## Build
Push `companion.py`, `requirements.txt`, and `.github/workflows/build-windows-exe.yml` to the repository root. In GitHub, open Actions and run **Build FLX.AI Windows Companion**. Download the `FLXAI-Companion-Windows` artifact and extract it.

## Test the companion before opening the website
Run `FLXAI-Companion.exe`. In the same browser on the same PC, open:
`http://127.0.0.1:8765/health`
It should display JSON with `"ok": true`.

Then open the hosted website and test `Open Notepad`. If the health page works but the website says it cannot connect, check the browser's local-network access permission for the website. The website and companion must be used on the same Windows PC.

## Notes
- Some apps may not be installed or may use different executable names on a given PC.
- Brightness control depends on monitor hardware/driver support.
- Do not run on a computer where you lack permission to launch applications or change settings.
