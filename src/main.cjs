const { app, BrowserWindow, Menu, Tray, nativeImage, screen, globalShortcut, ipcMain } = require('electron');
const fs = require('node:fs');
const path = require('node:path');

const APP_ID = 'com.aris.assistant';
const HOTKEY = 'CommandOrControl+Alt+Shift+A';
let overlay;
let tray;
let status = 'idle';
let showOverlay = true;
let startWithWindows = true;
let quitting = false;

function settingsPath() {
  return path.join(app.getPath('userData'), 'settings.json');
}

function loadSettings() {
  try {
    const parsed = JSON.parse(fs.readFileSync(settingsPath(), 'utf8'));
    return { startWithWindows: parsed.startWithWindows !== false };
  } catch {
    return { startWithWindows: true };
  }
}

function saveSettings() {
  fs.mkdirSync(app.getPath('userData'), { recursive: true });
  fs.writeFileSync(settingsPath(), JSON.stringify({ startWithWindows }, null, 2), { mode: 0o600 });
}

function applyStartupSetting() {
  if (process.platform !== 'win32') return;
  if (!app.isPackaged) {
    // Never register a development executable from a temporary or project path.
    app.setLoginItemSettings({ openAtLogin: false, path: process.execPath });
    return;
  }
  app.setLoginItemSettings({ openAtLogin: startWithWindows, openAsHidden: true });
}

function placeOverlay() {
  if (!overlay) return;
  const area = screen.getPrimaryDisplay().workArea;
  const margin = 18;
  const [width] = overlay.getSize();
  overlay.setPosition(area.x + area.width - width - margin, area.y + margin);
}

function setStatus(nextStatus) {
  const allowed = new Set(['idle', 'listening', 'thinking', 'working', 'speaking', 'paused']);
  if (!allowed.has(nextStatus)) return;
  status = nextStatus;
  if (overlay && !overlay.isDestroyed()) overlay.webContents.send('aris:status', status);
  updateTrayMenu();
}

function showOrHideOverlay() {
  if (!overlay) return;
  showOverlay = !showOverlay;
  if (showOverlay) {
    placeOverlay();
    overlay.showInactive();
  } else {
    overlay.hide();
  }
  updateTrayMenu();
}

function updateTrayMenu() {
  if (!tray) return;
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: showOverlay ? 'Hide status overlay' : 'Show status overlay', click: showOrHideOverlay },
    { label: `Status: ${status}`, enabled: false },
    { type: 'separator' },
    {
      label: app.isPackaged ? 'Start ARIS with Windows' : 'Start with Windows (available in installed build)',
      type: 'checkbox',
      checked: app.isPackaged && startWithWindows,
      enabled: app.isPackaged,
      click: (item) => {
        startWithWindows = item.checked;
        saveSettings();
        applyStartupSetting();
        updateTrayMenu();
      }
    },
    { type: 'separator' },
    { label: 'Quit ARIS', click: () => { quitting = true; app.quit(); } }
  ]));
}

function createTray() {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><circle cx="16" cy="16" r="14" fill="#071522" stroke="#38d8ff" stroke-width="2"/><path d="M8 17h5l3-8 4 14 3-6h2" fill="none" stroke="#8df1ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const icon = nativeImage.createFromDataURL(`data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`);
  tray = new Tray(icon);
  tray.setToolTip('ARIS — desktop assistant');
  tray.on('click', showOrHideOverlay);
  updateTrayMenu();
}

function createOverlay() {
  overlay = new BrowserWindow({
    width: 300,
    height: 92,
    show: false,
    frame: false,
    transparent: true,
    resizable: false,
    minimizable: false,
    maximizable: false,
    fullscreenable: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    hasShadow: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      webSecurity: true
    }
  });

  overlay.setAlwaysOnTop(true, 'floating');
  overlay.setIgnoreMouseEvents(true, { forward: true });
  overlay.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  overlay.once('ready-to-show', () => {
    if (showOverlay) {
      placeOverlay();
      overlay.showInactive();
    }
    overlay.webContents.send('aris:status', status);
  });
  overlay.on('close', (event) => {
    if (!quitting) {
      event.preventDefault();
      overlay.hide();
      showOverlay = false;
      updateTrayMenu();
    }
  });
  overlay.on('closed', () => { overlay = null; });
}

function registerShortcuts() {
  globalShortcut.register(HOTKEY, showOrHideOverlay);
}

app.setAppUserModelId(APP_ID);
app.on('before-quit', () => { quitting = true; });
app.on('window-all-closed', (event) => { event.preventDefault(); });

app.whenReady().then(() => {
  if (!app.requestSingleInstanceLock()) {
    app.quit();
    return;
  }

  ({ startWithWindows } = loadSettings());
  applyStartupSetting();
  createOverlay();
  createTray();
  registerShortcuts();

  app.on('second-instance', () => {
    if (overlay && !overlay.isDestroyed()) {
      showOverlay = true;
      placeOverlay();
      overlay.showInactive();
      updateTrayMenu();
    }
  });

  screen.on('display-metrics-changed', placeOverlay);
});

app.on('will-quit', () => globalShortcut.unregisterAll());

ipcMain.handle('aris:get-status', () => status);
