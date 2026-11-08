# Developer guide

## Prerequisites

- Windows 10/11 x64.
- Node.js LTS and npm.
- Python 3.11 or later.
- Windows microphone access enabled for desktop apps. ARIS starts with its microphone disarmed; it opens the selected input only after you enable “Microphone wake word” from the notification-area tray menu.
- Ollama for local language-model replies; `qwen3:8b` is the default model.
- The project pins its desktop runtime in `package.json`; run `npm install` from the repository root.

## Run

```powershell
npm start
```

For live diagnostics, run `npm run debug`. This opens ARIS with a Debug Console window and prints app/worker logs to the launching terminal. For an installed build, start `ARIS.exe --aris-debug`; the same console opens. Debug launches do not modify the Windows startup setting. Logs are also written to `%LOCALAPPDATA%\ARIS\logs\aris.log`. Diagnostic logs omit recognized speech and assistant replies. If the worker crashes while wake mode is enabled, ARIS retries up to three times; open the Debug Console for the exit code and Python/PortAudio error.

### One-time offline voice setup

Run `powershell -NoProfile -File scripts/setup_voice.ps1`. It installs pinned Python voice packages into `%LOCALAPPDATA%\ARIS\venv` and downloads the Vosk Indian-English model to `%LOCALAPPDATA%\ARIS\models`. The [official Vosk model page](https://alphacephei.com/vosk/models) lists the small Indian-English model at about 36 MB; it is downloaded once and is not stored in Git.

ARIS uses Vosk for offline speech recognition, Windows System.Speech for offline speech output, and only the local Ollama API at `127.0.0.1:11434` for replies. It sends no microphone audio to a cloud speech service and stores no transcript history in this section. If `qwen3:8b` is absent, run `ollama pull qwen3:8b`.

Open “Audio Settings…” from the tray to detect microphones/speakers and Windows defaults, choose ARIS-specific routes (device host and native rate are shown), enable or disable voice-driven switching, or open Windows microphone privacy controls. Detection and format probing do not open the microphone. When wake listening starts, ARIS selects a sample rate accepted by the chosen input device. From the tray menu, turn on “Microphone wake word”; ARIS then listens locally for “ARIS” or “Hey ARIS.” Turn the same tray item off to close the microphone stream. Listening is always off after app startup, including Windows startup. After the wake acknowledgment or first recognized command, ARIS enters conversation mode and accepts follow-up requests without repeating the wake word. Audio Settings lets you choose a 10, 15, or 20-second silence timeout. Once that much silence is detected, ARIS returns to wake-word standby. While ARIS processes a request or speaks, microphone capture pauses and resumes afterward if wake listening remains enabled.

Press `Ctrl+Alt+Shift+X` to cancel a request or stop speech. There is no push-to-talk hotkey. With voice switching enabled, say “switch ARIS microphone to <listed device name>” or “switch ARIS output to <listed device name>”. Say “switch ARIS microphone to default” or “switch ARIS output to default” to return to the Windows default.

### Section 3 local actions

ARIS recognizes `open Chrome`, `open Gmail`, `search YouTube for <words>`, `open the first video`, `find the file named <words>`, and other listed fixed intents. ARIS also accepts a single multi-step request such as “open YouTube, search for MrBeast Gaming videos, and play one of the videos.” It resolves the first video result and opens it in Chrome; if YouTube changes its result markup, it opens the matching results page instead. During conversation mode, follow-up phrases such as “play one of the videos” use the last YouTube query. Gmail is only opened in Chrome; the app does not read or send messages. File search checks filenames only, inside folders you explicitly add to `approved_roots.json` in the Electron user-data directory (normally `%APPDATA%\aris-desktop`). Start with an empty file or use `{"roots":["C:\\Users\\<your-name>\\Documents"]}`. Use the tray menu’s “Open local action log” item to inspect `action-log.json`. It records only time, action key, and outcome, up to 100 entries.

Say “remember that …” to save a preference and “list preferences” to review them by voice. Use the tray menu’s “Open saved preferences” item to edit or delete entries in `preferences.json`. Preferences are loaded into local model context as untrusted personalization, and should never include secrets.

Run `npm run test:tools` for local action and preference tests.

Speech output uses a short-lived Windows PowerShell process with System.Speech for each utterance. The WAV is synthesized before the audio device is opened for playback, and errors are recorded in the debug log. The output route is applied during playback.

The app is designed to stay in the notification area when its window is closed. Use the tray menu to show the overlay or exit. The overlay itself is mouse-transparent. The installed build registers for user login by default. Toggle “Start ARIS with Windows” from the tray menu. Startup registration is per-user; development runs do not register themselves.

## Build a Windows installer

Install dependencies with `npm install`, then run `npm run pack:win` for an unpacked smoke build or `npm run dist:win` for the per-user NSIS installer in `dist/`. The installer is unsigned in this MVP, so Windows may show an unknown-publisher notice. The app does not install Python or Ollama. After installation, use the tray menu’s “Set up offline voice” action to install the pinned local Python packages and download the Vosk model. This step downloads the model once from the official Vosk host.

The installer uses electron-builder’s NSIS target in assisted per-user mode, with a selectable install directory and no elevation request by default. See the [NSIS configuration reference](https://www.electron.build/docs/nsis/).

## Project layout

```text
src/main.cjs       Electron main process and lifecycle
src/preload.cjs    Restricted context bridge
src/renderer/      Status overlay and voice feedback
src/tools/         Fixed local action parser, allowlisted tools, and tests
src/preferences.cjs Explicit local preference store
src/audio.cjs       Audio route validation and voice intent parser
scripts/smoke_audio_devices.py  Device enumeration and ID resolution without opening streams
scripts/smoke_audio_route.py    SAPI file synthesis with mocked speaker playback
scripts/smoke_wake_word.py      Offline wake phrase, acknowledgment, and command parsing
src/renderer/settings.* Clickable audio settings window
package-lock.json   Pinned npm dependency tree
voice/             Offline voice worker and pinned Python dependencies
scripts/           Voice setup and offline smoke checks
docs/              Architecture, security, plan, and development notes
USER_RULES.md      Empty owner-authored rules file
```

## Contribution workflow

Keep changes focused on one project section. Update the project plan, architecture/security notes, and this guide when behavior changes. Run `npm run check`, `npm run test:tools`, and `npm run pack:win` on Windows, `python scripts/smoke_voice.py <model-folder>`, and `python scripts/smoke_worker.py <model-folder>`, and `python scripts/smoke_audio_devices.py` plus `python scripts/smoke_audio_route.py`. These offline checks use generated speech and do not open the microphone. Then manually verify tray wake-word on/off, wake-word detection, and audible routed output on the target PC before release. The runtime may be installed into a temporary dependency directory if the workspace does not support package installation.

Do not commit provider credentials, user data, recordings, screenshots, logs, local preferences, or generated build output. Use `.env.example` only for variable names with blank values; real credentials belong in OS-protected storage.
