const test = require('node:test');
const assert = require('node:assert/strict');
const { parseAudioRequest, resolveDevice, validateAudioSettings } = require('./audio.cjs');

const devices = [
  { id: 'mic-1', name: 'USB Microphone', hostApi: 'WASAPI' },
  { id: 'out-1', name: 'Speakers (Realtek)', hostApi: 'WASAPI' },
  { id: 'out-2', name: 'Speakers (Realtek)', hostApi: 'DirectSound' }
];

test('parses only clear ARIS microphone and output switching phrases', () => {
  assert.deepEqual(parseAudioRequest('switch ARIS microphone to USB Microphone'), { kind: 'input', query: 'USB Microphone' });
  assert.deepEqual(parseAudioRequest('please change the ARIS output to Speakers (Realtek)'), { kind: 'output', query: 'Speakers (Realtek)' });
  assert.equal(parseAudioRequest('change my mind about the microphone'), null);
});

test('resolves exact names, unique partial names, and default without ambiguity', () => {
  assert.deepEqual(resolveDevice('USB Microphone', devices), { id: 'mic-1', name: 'USB Microphone' });
  assert.equal(resolveDevice('Realtek', devices).error.includes('more than one'), true);
  assert.equal(resolveDevice('speakers', devices).error.includes('more than one'), true);
  assert.deepEqual(resolveDevice('Speakers (Realtek) — WASAPI', devices), { id: 'out-1', name: 'Speakers (Realtek)' });
  assert.deepEqual(resolveDevice('system default', devices), { id: '', name: 'Windows default' });
});

test('validates persisted choices against the discovered device list', () => {
  assert.deepEqual(validateAudioSettings({ inputDeviceId: 'bad', outputDeviceId: 'out-2', allowVoiceDeviceSwitching: true }, { inputs: devices.slice(0, 1), outputs: devices.slice(1) }), { inputDeviceId: '', outputDeviceId: 'out-2', allowVoiceDeviceSwitching: true });
});
