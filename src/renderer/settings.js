const inputSelect = document.getElementById('inputDevice');
const outputSelect = document.getElementById('outputDevice');
const inputDetected = document.getElementById('inputDetected');
const outputDetected = document.getElementById('outputDetected');
const allowVoiceSwitching = document.getElementById('voiceSwitching');
const status = document.getElementById('status');
const refreshButton = document.getElementById('refresh');
const saveButton = document.getElementById('save');
let currentSettings;
let currentDevices;

function setBusy(busy) {
  refreshButton.disabled = busy;
  saveButton.disabled = busy;
}

function fillSelect(select, devices, defaultId, selectedId, label) {
  select.replaceChildren();
  const defaultDevice = devices.find((device) => device.id === defaultId);
  const fallback = document.createElement('option');
  fallback.value = '';
  fallback.textContent = 'Windows default' + (defaultDevice ? ' — ' + defaultDevice.name : '');
  select.append(fallback);
  for (const device of devices) {
    const option = document.createElement('option');
    option.value = device.id;
    option.textContent = device.name + ' — ' + device.hostApi;
    select.append(option);
  }
  if (selectedId && !devices.some((device) => device.id === selectedId)) {
    const missing = document.createElement('option');
    missing.value = selectedId;
    missing.textContent = 'Saved ' + label + ' is unavailable — refresh or choose another';
    select.append(missing);
  }
  select.value = selectedId || '';
  return defaultDevice;
}

function render(data) {
  currentSettings = data.settings;
  currentDevices = data.devices;
  const defaultInput = fillSelect(inputSelect, currentDevices.inputs, currentDevices.defaultInputId, currentSettings.inputDeviceId, 'microphone');
  const defaultOutput = fillSelect(outputSelect, currentDevices.outputs, currentDevices.defaultOutputId, currentSettings.outputDeviceId, 'speaker');
  const selectedInput = currentDevices.inputs.find((device) => device.id === currentSettings.inputDeviceId);
  const selectedOutput = currentDevices.outputs.find((device) => device.id === currentSettings.outputDeviceId);
  inputDetected.textContent = 'Windows default: ' + (defaultInput?.name || 'none detected') + ' · ARIS route: ' + (selectedInput ? selectedInput.name + ' — ' + selectedInput.hostApi : 'Windows default');
  outputDetected.textContent = 'Windows default: ' + (defaultOutput?.name || 'none detected') + ' · ARIS route: ' + (selectedOutput ? selectedOutput.name + ' — ' + selectedOutput.hostApi : 'Windows default');
  allowVoiceSwitching.checked = currentSettings.allowVoiceDeviceSwitching;
  status.textContent = currentDevices.inputs.length + ' microphone(s), ' + currentDevices.outputs.length + ' output device(s) found. Detection did not open them.';
}

async function loadDevices(refresh = false) {
  setBusy(true);
  status.textContent = refresh ? 'Refreshing device list…' : 'Detecting audio devices…';
  try {
    const data = refresh ? { settings: currentSettings, devices: await window.aris.refreshAudioDevices() } : await window.aris.getAudioSettings();
    render(data);
  } catch (error) {
    status.textContent = String(error?.message || 'Could not detect audio devices.');
  } finally { setBusy(false); }
}

saveButton.addEventListener('click', async () => {
  setBusy(true);
  status.textContent = 'Saving ARIS audio settings…';
  try {
    const result = await window.aris.saveAudioSettings({
      inputDeviceId: inputSelect.value,
      outputDeviceId: outputSelect.value,
      allowVoiceDeviceSwitching: allowVoiceSwitching.checked
    });
    render(result);
    status.textContent = 'Saved. The microphone choice applies to wake-word listening.';
  } catch (error) {
    status.textContent = String(error?.message || 'Could not save audio settings.');
  } finally { setBusy(false); }
});

refreshButton.addEventListener('click', () => loadDevices(true));
document.getElementById('openPrivacy').addEventListener('click', async () => {
  try { await window.aris.openMicrophonePrivacySettings(); }
  catch { status.textContent = 'Windows microphone privacy settings could not be opened.'; }
});

void loadDevices();
