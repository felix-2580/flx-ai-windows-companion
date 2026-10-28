# FLX.AI Windows Companion

A Windows-only companion that performs a small, allow-listed set of local Windows actions when commands arrive from the FLX.AI hosted web UI. The companion binds to `127.0.0.1` only; it is not a network-wide remote-control server.

## Supported commands

- `Open Notepad`, `Open Calculator`, `Open Paint`, `Open File Explorer`, `Open Task Manager`, `Open Settings`
- `Increase volume`, `Decrease volume`, `Set volume to 50 percent`, `Mute volume`
- `Increase brightness`, `Decrease brightness`, `Set brightness to 50 percent` (hardware support varies)
- `Switch window`, `Minimize window`, `Maximize window`, `Show desktop`
- `Help`

Unknown commands are not passed to a shell. The companion does not run arbitrary code, download or delete files, or execute unrestricted terminal commands.

## Build an EXE locally

On a Windows computer with Python 3.11 installed:

1. Extract this folder.
2. Double-click `build_exe.bat`.
3. When it finishes, the executable is at `dist\\FLXAI-Companion.exe`.
4. Run it and keep the console window open while using the website.

## Build via GitHub Actions (no Python needed on your PC)

1. Upload the contents of this folder to a GitHub repository (including `.github/workflows/build-windows-exe.yml`).
2. Open the repository's **Actions** tab.
3. Choose **Build FLX.AI Windows Companion** → **Run workflow**.
4. When the run succeeds, open that run and download the `FLXAI-Companion-Windows` artifact. It downloads as a ZIP containing the EXE.
5. Extract the ZIP and upload the EXE to your own Google Drive if desired.

## Connect the hosted website

The companion listens at `http://127.0.0.1:8765`. The updated `website/templates/index.html` tries this local endpoint first, then falls back to the hosted demo API if the companion is not running. Replace `templates/index.html` in the Render-connected web repo with this file and commit it; Render will redeploy.

## Notes

- The browser must have microphone permission for voice input.
- The companion must be running on the same Windows computer that you want to control.
- Some school-managed PCs block downloaded executables or restrict microphone/system controls. Do not bypass those policies; ask the school administrator.
- Windows or antivirus may show a warning for a self-built EXE because it is not code-signed. Only run builds you have inspected and trust.
- Brightness control depends on the display and driver. Volume control depends on Windows audio support.
