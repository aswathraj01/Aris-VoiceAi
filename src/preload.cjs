const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('aris', Object.freeze({
  getStatus: () => ipcRenderer.invoke('aris:get-status'),
  onStatus: (callback) => {
    if (typeof callback !== 'function') return () => {};
    const listener = (_event, value) => callback(value);
    ipcRenderer.on('aris:status', listener);
    return () => ipcRenderer.removeListener('aris:status', listener);
  }
}));
