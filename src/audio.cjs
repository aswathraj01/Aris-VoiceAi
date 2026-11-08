const DEFAULT_AUDIO_SETTINGS = Object.freeze({ inputDeviceId: '', outputDeviceId: '', allowVoiceDeviceSwitching: false });

function parseAudioRequest(input) {
  const text = String(input || '').trim().replace(/[.!?]+$/, '');
  const prefix = "^(?:hey\\s+aris[, ]*)?(?:please\\s+)?(?:switch|change|set|use)\\s+(?:(?:the|my)\\s+)?(?:aris(?:'s)?\\s+)?";
  const inputMatch = text.match(new RegExp(prefix + '(?:microphone|mic|input)(?:\\s+to)?\\s+(.+)$', 'i'));
  if (inputMatch) return { kind: 'input', query: inputMatch[1].trim() };
  const outputMatch = text.match(new RegExp(prefix + '(?:audio\\s+output|speaker|speakers|headphones|output)(?:\\s+to)?\\s+(.+)$', 'i'));
  if (outputMatch) return { kind: 'output', query: outputMatch[1].trim() };
  return null;
}

function resolveDevice(query, devices, defaultId = '') {
  const normalized = String(query || '').trim().replace(/^['\"]|['\"]$/g, '').toLocaleLowerCase();
  if (['default', 'system default', 'windows default'].includes(normalized)) return { id: '', name: 'Windows default' };
  const candidates = (Array.isArray(devices) ? devices : []).filter((device) =>
    typeof device.id === 'string' && typeof device.name === 'string'
  );
  const exact = candidates.filter((device) => {
    const name = device.name.toLocaleLowerCase();
    const fullName = (device.name + ' — ' + String(device.hostApi || '')).toLocaleLowerCase();
    return name === normalized || fullName === normalized;
  });
  if (exact.length === 1) return { id: exact[0].id, name: exact[0].name };
  if (exact.length > 1) return { error: 'More than one audio device has that name. Choose it in Audio Settings.' };
  const partial = candidates.filter((device) => {
    const fullName = (device.name + ' — ' + String(device.hostApi || '')).toLocaleLowerCase();
    return fullName.includes(normalized);
  });
  if (partial.length === 1) return { id: partial[0].id, name: partial[0].name };
  if (partial.length > 1) return { error: 'That matches more than one device. Choose the exact device name in Audio Settings.' };
  return { error: 'I could not find an available audio device matching that name.' };
}

function validateAudioSettings(value, devices) {
  const inputDevices = Array.isArray(devices?.inputs) ? devices.inputs : [];
  const outputDevices = Array.isArray(devices?.outputs) ? devices.outputs : [];
  const inputDeviceId = typeof value?.inputDeviceId === 'string' && inputDevices.some((device) => device.id === value.inputDeviceId) ? value.inputDeviceId : '';
  const outputDeviceId = typeof value?.outputDeviceId === 'string' && outputDevices.some((device) => device.id === value.outputDeviceId) ? value.outputDeviceId : '';
  return { inputDeviceId, outputDeviceId, allowVoiceDeviceSwitching: value?.allowVoiceDeviceSwitching === true };
}

function audioSettingsFromFile(filePath) {
  const fs = require('node:fs');
  try {
    const value = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    return {
      inputDeviceId: typeof value.audioInputDeviceId === 'string' ? value.audioInputDeviceId.slice(0, 500) : '',
      outputDeviceId: typeof value.audioOutputDeviceId === 'string' ? value.audioOutputDeviceId.slice(0, 500) : '',
      allowVoiceDeviceSwitching: value.allowVoiceDeviceSwitching === true
    };
  } catch { return { ...DEFAULT_AUDIO_SETTINGS }; }
}

module.exports = { DEFAULT_AUDIO_SETTINGS, audioSettingsFromFile, parseAudioRequest, resolveDevice, validateAudioSettings };
