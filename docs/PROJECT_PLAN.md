# ARIS MVP project plan

**Owner:** Aswath Raj  
**Start:** November 8, 2026  
**Target first release:** December 8, 2026

## Goal

Deliver a useful, reviewable Windows assistant MVP that can hear a spoken request, respond naturally, and perform a limited set of approved desktop tasks. The first month is a foundation, not a promise of general human-level computer ability.

## Sections and acceptance criteria

1. **Foundation and desktop shell** — repository documentation, clean application structure, always-on-top top-right status overlay, and tray lifecycle. Startup registration is available only in the installed build; Section 5 adds a per-user startup toggle. The overlay is mouse-transparent; tray controls remain available.
2. **Voice conversation** — offline Vosk wake-word recognition, local Windows SAPI speech, explicit tray on/off control (off at startup), cancel behavior, local Ollama replies, and visible armed/listening/thinking/speaking states.
3. **Safe task tools** — complete for the initial read-only scope: deterministic Chrome/Gmail launch and filename-only search in explicitly approved folders, plus a tray-accessible local action log. No arbitrary shell execution. Consequential actions remain out of scope until a confirmation broker exists.
4. **Preferences and memory** — complete for the local MVP: “remember …” captures only explicit preferences; a tray item opens the JSON store for review, editing, or deletion. Preferences cannot grant permissions or change code.
5. **Integration and release** — manual walkthroughs on the target Windows machine, audio settings for enumerating/selecting mic and output devices, explicit consent for voice-driven routing, setup documentation, known limitations, and a tagged MVP release.

## Calendar

| Window | Target |
| --- | --- |
| Nov 8–14 | Section 1: shell, overlay, startup/tray controls, repository documentation |
| Nov 15–21 | Section 2: voice loop and provider boundary |
| Nov 22–28 | Section 3: first safe computer actions |
| Nov 29–Dec 5 | Section 4: user-controlled preference memory |
| Dec 6–8 | Section 5: integration walkthrough and release notes |

Dates are planning targets. Progress depends on the available Windows SDKs, provider access, and hands-on device checks. Each section is documented, checked, and pushed as a separate GitHub update before moving to the next.

## Out of scope for the first month

- “Every task a human can do” or guaranteed superiority to any existing model.
- Self-modifying code, self-granted permissions, or unsupervised external actions.
- Broad indexing of the computer or silent collection of personal data.
- Unattended work after the developer or owner ends an active session.

## Completion record

| Section | Status | Notes |
| --- | --- | --- |
| 1. Foundation and desktop shell | Complete | Documentation, safe Electron shell, overlay, tray lifecycle, and blank rules file are in place. `npm run check` passed; a live Windows launch displayed the top-right Ready overlay. Startup installer wiring remains in Section 5. |
| 2. Voice conversation | In progress | Offline TTS-to-Vosk, wake-word plus command parsing, configurable conversation silence timeout, native Windows SAPI WAV synthesis, and worker model-load/shutdown checks pass. Audio device enumeration reports Windows defaults without capturing audio. Offline “Hey Iris” phrase/command parsing and wake acknowledgment configuration pass. Unexpected voice-worker exits now retry up to three times, and debug mode captures local worker stderr. Manual tray toggle, live wake-word, and routed-output checks remain. |
| 3. Safe task tools | In progress | Chrome/Gmail launch and allowlisted filename search are implemented; YouTube search and first-result navigation are implemented with deterministic intents; command and top-result tests are included. Live voice-to-Chrome walkthrough awaits the owner’s microphone trial. No mailbox reading or sending. |
| 4. Preferences and memory | Complete | Explicit remember/list requests, local editable JSON store, tray access, and bounded preference injection into local replies. `npm run test:tools` covers capture, deduplication, and editing. |
| 5. Integration and release | In progress | Windows NSIS build passes. Clickable audio settings enumerate endpoints, show Windows defaults, and save ARIS-only routes; nine unit tests plus no-capture enumeration/routing smokes pass. Offline wake and command parsing, bounded worker restart, and debug log behavior are implemented. Manual tray wake toggle, live microphone, acknowledgment playback, and routed-output walkthroughs remain. |
