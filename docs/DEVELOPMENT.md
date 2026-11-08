# Developer guide

## Prerequisites

- Windows 10/11 x64.
- Node.js LTS and npm.
- The project pins its desktop runtime in `package.json`; run `npm install` from the repository root.

## Run

```powershell
npm start
```

The app is designed to stay in the notification area when its window is closed. Use the tray menu to show the overlay or exit. The overlay itself is mouse-transparent and does not yet accept voice input in Section 1. The Windows startup preference will be active in the installed build after packaging is configured in Section 5.

## Project layout

```text
src/main.cjs       Electron main process and lifecycle
src/preload.cjs    Restricted context bridge
src/renderer/      Status-only overlay
docs/              Architecture, security, plan, and development notes
USER_RULES.md      Empty owner-authored rules file
```

## Contribution workflow

Keep changes focused on one project section. Update the project plan, architecture/security notes, and this guide when behavior changes. Run `npm run check`, launch the app on Windows, manually inspect the overlay, and record the exact result and limitations in the section update before pushing. The runtime may be installed into a temporary dependency directory if the workspace does not support package installation.

Do not commit provider credentials, user data, recordings, screenshots, logs, local preferences, or generated build output. Use `.env.example` only for variable names with blank values; real credentials belong in OS-protected storage.
