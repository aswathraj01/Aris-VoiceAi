# ARIS architecture

## Design principles

- Run the desktop shell and local orchestration on the user's Windows account.
- Keep the user interface, model/provider adapter, task planner, and individual tools separated.
- Give each tool a narrow capability. The assistant model can propose an action; a policy layer decides whether it is allowed and whether user confirmation is required.
- Treat files, web pages, email, and model responses as untrusted input, not as instructions that can grant new access.
- Keep user memory local and editable. Record user-approved preferences rather than training or changing model weights.

## Planned components

```text
Windows desktop shell
  ├─ Status overlay (idle / listening / thinking / working / speaking / paused)
  ├─ Tray controls, startup preference, and clickable audio settings
  └─ Restricted preload bridge
       ↓ typed IPC
Local assistant coordinator
  ├─ Voice adapter (speech-to-text and text-to-speech)
  ├─ Audio device enumerator and per-ARIS route selection
  ├─ Conversation/model adapter
  ├─ Policy and confirmation broker
  ├─ Task planner
  ├─ Allowlisted computer tools
  └─ Local preference store and redacted action history
```

The model adapter can be swapped later. Fixed deterministic intents route the first tools directly; model responses cannot invoke tools. The first MVP makes provider traffic explicit: audio stays local, and the current turn text goes only to the loopback Ollama service. No file or email content is sent. Section 3 can search names only in folders on the local approved-roots list.

## Current implementation section

Section 2 adds tray-controlled offline wake-word listening. Listening starts only after the owner enables “Microphone wake word” in the Windows notification-area tray menu; every app launch begins disarmed. The Python worker uses a constrained Vosk grammar to detect “ARIS” or “Hey ARIS” locally, then transcribes the request locally. It closes the input stream while a request is processed and while pyttsx3 speaks. Each speech clip is synthesized in an isolated, 30-second-bounded process before playback, preventing a stuck Windows SAPI engine from wedging later turns. The Electron coordinator sends only the current transcript to the loopback Ollama chat API. No transcript history is persisted. Unexpected worker exits are logged locally and retried up to three times while wake listening remains enabled; the opt-in debug console displays worker stderr without recording transcripts. Section 3 adds fixed local tools that do not use model-generated commands.

## Audio settings and device routing

The tray opens a separate clickable settings window. A small Python query lists available input/output endpoints, the Windows defaults, supported default sample rates, and host API labels; it never opens a capture or playback stream. The voice worker probes supported input formats without opening a capture stream and uses a supported/native sample rate for recognition. The owner can select ARIS-specific input/output routes and optionally allow deterministic voice requests to change those routes. The microphone stream is opened only while the owner has explicitly enabled wake-word listening, and closes when they turn it off. Output selection routes synthesized audio to the chosen endpoint without changing the Windows system default.

## Section 5 packaging boundary

The Windows build packages the Electron app and the small Python worker, while keeping Python packages, the Vosk model, Ollama, settings, preferences, approved folder roots, and action history outside the installer payload. A visible tray action starts the fixed voice setup script. Startup registration is available only from an installed build and can be disabled in the tray menu.

## Section 4 local preferences

Only a deterministic “remember …” request writes a preference. “List preferences” reads the saved entries. The tray opens `preferences.json` in the system’s default editor so the owner can review, edit, or remove entries. The coordinator reads this file for each model turn and adds the text as untrusted personalization context. Preferences cannot enable tools, override fixed safety rules, or alter code. The store keeps at most 40 entries of up to 300 characters each.

## Section 3 local tools

The coordinator recognizes only three initial task patterns: open Chrome, open Gmail in Chrome, and search for a filename. The first two launch a fixed executable/URL without a shell. Search traverses only valid local directories from `%APPDATA%\aris-desktop\approved_roots.json` (actual app-data folder varies by Windows profile), skips symlinks and common system/dependency directories, and returns names only. Traversal has depth, entry, and result limits. A local `action-log.json` stores the timestamp, action name, and outcome for the latest 100 actions; it excludes prompts and filenames. Gmail launch opens the site and does not read or send mail.

## Planned request flow

1. Capture speech only while the user has enabled listening.
2. Convert speech to a request and show the `thinking` state.
3. Ask the model for a response or a structured tool proposal.
4. Validate the proposal against the fixed policy and user rules.
5. Ask for confirmation when required; execute only the matching registered tool.
6. Report the real result and write a redacted audit event.
7. Offer a correction as a preference candidate; save it only after explicit approval.
