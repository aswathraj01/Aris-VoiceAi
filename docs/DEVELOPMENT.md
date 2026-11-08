# Developer guide

## Prerequisites

- Windows 10/11 x64.
- Node.js LTS and npm.
- Python 3.11 or later.
- Windows microphone access enabled for desktop apps. ARIS asks Windows to open the default input only after push-to-talk starts.
- Ollama for local language-model replies; `qwen3:8b` is the default model.
- The project pins its desktop runtime in `package.json`; run `npm install` from the repository root.

## Run

```powershell
npm start
```

### One-time offline voice setup

Run `powershell -NoProfile -File scripts/setup_voice.ps1`. It installs pinned Python voice packages into `%LOCALAPPDATA%\ARIS\venv` and downloads the Vosk Indian-English model to `%LOCALAPPDATA%\ARIS\models`. The [official Vosk model page](https://alphacephei.com/vosk/models) lists the small Indian-English model at about 36 MB; it is downloaded once and is not stored in Git.

ARIS uses Vosk for offline speech recognition, Windows SAPI through `pyttsx3` for offline speech output, and only the local Ollama API at `127.0.0.1:11434` for replies. It sends no microphone audio to a cloud speech service and stores no transcript history in this section. If `qwen3:8b` is absent, run `ollama pull qwen3:8b`.

Press `Ctrl+Alt+Shift+V` once to start capture and again to stop and get a response. Press `Ctrl+Alt+Shift+X` to cancel. Pause/resume from the tray. The microphone is opened only during the visible Listening state; there is no always-on wake word in this MVP. Use `Ctrl+Alt+Shift+X` to cancel a request or stop speech.

### Section 3 local actions

ARIS recognizes `open Chrome`, `open Gmail`, and `find the file named <words>`. Gmail is only opened in Chrome; the app does not read or send messages. File search checks filenames only, inside folders you explicitly add to `approved_roots.json` in the Electron user-data directory (normally `%APPDATA%\aris-desktop`). Start with an empty file or use `{"roots":["C:\\Users\\<your-name>\\Documents"]}`. Use the tray menu’s “Open local action log” item to inspect `action-log.json`. It records only time, action key, and outcome, up to 100 entries.

Run `npm run test:tools` for the local action tests.

The app is designed to stay in the notification area when its window is closed. Use the tray menu to show the overlay or exit. The overlay itself is mouse-transparent. The Windows startup preference will be active in the installed build after packaging is configured in Section 5.

## Project layout

```text
src/main.cjs       Electron main process and lifecycle
src/preload.cjs    Restricted context bridge
src/renderer/      Status overlay and voice feedback
src/tools/         Fixed local action parser, allowlisted tools, and tests
voice/             Offline voice worker and pinned Python dependencies
scripts/           Voice setup and offline smoke checks
docs/              Architecture, security, plan, and development notes
USER_RULES.md      Empty owner-authored rules file
```

## Contribution workflow

Keep changes focused on one project section. Update the project plan, architecture/security notes, and this guide when behavior changes. Run `npm run check`, `npm run test:tools`, `python scripts/smoke_voice.py <model-folder>`, and `python scripts/smoke_worker.py <model-folder>`. These offline checks use generated speech and do not open the microphone. Then manually verify the push-to-talk hotkey and audio on the target PC before release. The runtime may be installed into a temporary dependency directory if the workspace does not support package installation.

Do not commit provider credentials, user data, recordings, screenshots, logs, local preferences, or generated build output. Use `.env.example` only for variable names with blank values; real credentials belong in OS-protected storage.
