# ARIS MVP project plan

**Owner:** Aswath Raj  
**Start:** November 8, 2026  
**Target first release:** December 8, 2026

## Goal

Deliver a useful, reviewable Windows assistant MVP that can hear a spoken request, respond naturally, and perform a limited set of approved desktop tasks. The first month is a foundation, not a promise of general human-level computer ability.

## Sections and acceptance criteria

1. **Foundation and desktop shell** — repository documentation, clean application structure, always-on-top top-right status overlay, and tray lifecycle. Startup registration is enabled only for an installed build and will be completed with packaging in Section 5. The overlay is mouse-transparent; tray controls remain available.
2. **Voice conversation** — offline Vosk recognition, local Windows SAPI speech, explicit push-to-talk, cancel/pause behavior, local Ollama replies, and visible listening/thinking/speaking states.
3. **Safe task tools** — complete for the initial read-only scope: deterministic Chrome/Gmail launch and filename-only search in explicitly approved folders, plus a tray-accessible local action log. No arbitrary shell execution. Consequential actions remain out of scope until a confirmation broker exists.
4. **Preferences and memory** — complete for the local MVP: “remember …” captures only explicit preferences; a tray item opens the JSON store for review, editing, or deletion. Preferences cannot grant permissions or change code.
5. **Integration and release** — manual walkthroughs on the target Windows machine, setup documentation, known limitations, and a tagged MVP release.

## Calendar

| Window | Target |
| --- | --- |
| Nov 8–14 | Section 1: shell, overlay, startup/tray controls, repository documentation |
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
| 2. Voice conversation | In progress | Offline TTS-to-Vosk smoke check passes; worker model-load/shutdown passes without opening the microphone; local Ollama responded to a synthetic prompt. User push-to-talk/microphone trial remains. |
| 3. Safe task tools | In progress | Initial actions implemented: Chrome/Gmail launch and allowlisted filename search. Automated tests pending; no mailbox reading or sending. | |
| 4. Preferences and memory | Complete | Explicit remember/list requests, local editable JSON store, tray access, and bounded preference injection into local replies. `npm run test:tools` covers capture, deduplication, and editing. | |
| 5. Integration and release | In progress | Windows NSIS installer and packaged offline voice setup are being wired. Still requires a built-installer smoke check and the owner’s live microphone walkthrough. | |
