# Security and privacy model

## Fixed controls

- User-editable rules can add preferences or make behavior more restrictive. They cannot override permission boundaries, disable confirmation for protected actions, or grant ARIS new capabilities.
- Do not execute model-generated shell commands, scripts, or source code.
- Expose only registered tools through the coordinator. Start with app launch and read-only search in owner-selected folders.
- Require confirmation before sending or deleting data, changing system settings, making purchases, or taking other consequential actions.
- Provide an immediate pause/quit path and show the active state in the overlay.
- Store provider credentials in Windows Credential Manager or an equivalent OS-protected store. Never put credentials in source files, logs, memory, screenshots, or Git.
- Keep action history local, minimal, and redacted. Provide a way to clear it.
- Keep local data outside the source repository and exclude it from Git.

## Provider and data boundary

The desktop shell can be local, while speech recognition or a language model may still send prompts or audio to a provider. Section 2 uses offline Vosk recognition and local Windows SAPI speech output. It sends recognized text only to the configured loopback Ollama endpoint, restricted to localhost/127.0.0.1/::1. It does not send microphone audio to a cloud provider. Microphone capture begins only after the user presses the voice hotkey and stops when they press it again, cancel, or pause. Audio and transcripts are not written to disk.

## User rules

`USER_RULES.md` is reserved for owner-authored behavior preferences. It is intentionally blank. The application must remain safe if the file is empty, malformed, or contains conflicting text; safety defaults come from code and this document.

## Incident note

The repository's earlier public history contained a credential-like value in a configuration file. Revoke that credential in its provider dashboard and do not reuse it. Removing the file in a later commit does not invalidate or erase the historical value. A separate history rewrite may be considered after the credential is revoked; it changes commit IDs and can disrupt existing clones.
