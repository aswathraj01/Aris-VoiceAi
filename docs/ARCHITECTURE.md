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
  ├─ Tray controls and startup preference
  └─ Restricted preload bridge
       ↓ typed IPC
Local assistant coordinator
  ├─ Voice adapter (speech-to-text and text-to-speech)
  ├─ Conversation/model adapter
  ├─ Policy and confirmation broker
  ├─ Task planner
  ├─ Allowlisted computer tools
  └─ Local preference store and redacted action history
```

The model adapter can be swapped later. The first MVP makes provider traffic explicit: audio stays local, and the current turn text goes only to the loopback Ollama service. No file or email content is sent in this section.

## Current implementation section

Section 2 adds user-triggered push-to-talk. A Python worker captures microphone audio only after the voice hotkey, Vosk transcribes it locally, and pyttsx3 speaks the result locally. The Electron coordinator sends only the current utterance to the loopback Ollama chat API and speaks the reply. No transcript history is persisted; there are no computer-action tools yet.

## Planned request flow

1. Capture speech only while the user has enabled listening.
2. Convert speech to a request and show the `thinking` state.
3. Ask the model for a response or a structured tool proposal.
4. Validate the proposal against the fixed policy and user rules.
5. Ask for confirmation when required; execute only the matching registered tool.
6. Report the real result and write a redacted audit event.
7. Offer a correction as a preference candidate; save it only after explicit approval.
