const { contextBridge, ipcRenderer } = require('electron');

function subscribe(channel, callback) {
  if (typeof callback !== 'function') return () => {};
  const listener = (_event, value) => callback(value);
  ipcRenderer.on(channel, listener);
  return () => ipcRenderer.removeListener(channel, listener);
}

contextBridge.exposeInMainWorld('aris', Object.freeze({
  getStatus: () => ipcRenderer.invoke('aris:get-status'),
  getDetail: () => ipcRenderer.invoke('aris:get-detail'),
  onStatus: (callback) => subscribe('aris:status', callback),
  onDetail: (callback) => subscribe('aris:detail', callback),
  onMessage: (callback) => subscribe('aris:message', callback),
  getDebugLog: () => ipcRenderer.invoke('aris:debug:get-log'),
  onDebugLog: (callback) => subscribe('aris:debug:entry', callback),
  getAudioSettings: () => ipcRenderer.invoke('aris:audio:get'),
  refreshAudioDevices: () => ipcRenderer.invoke('aris:audio:refresh'),
  saveAudioSettings: (settings) => ipcRenderer.invoke('aris:audio:save', settings),
  openMicrophonePrivacySettings: () => ipcRenderer.invoke('aris:audio:open-mic-privacy')
}));
