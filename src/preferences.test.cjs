const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { applyPreferenceRequest, parsePreferenceRequest, preferenceContext, readPreferences } = require('./preferences.cjs');

test('recognizes explicit remember and list requests only', () => {
  assert.deepEqual(parsePreferenceRequest('remember that I prefer short answers'), { action: 'remember', text: 'I prefer short answers' });
  assert.deepEqual(parsePreferenceRequest('please show my preferences'), { action: 'list' });
  assert.equal(parsePreferenceRequest('you should remember my password'), null);
});

test('stores preferences locally, deduplicates them, and makes them editable', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'aris-preferences-'));
  const file = path.join(dir, 'preferences.json');
  try {
    const request = parsePreferenceRequest('remember that I like concise replies');
    applyPreferenceRequest(file, request);
    applyPreferenceRequest(file, request);
    assert.equal(readPreferences(file).length, 1);
    assert.match(preferenceContext(file), /concise replies/);
    const editable = JSON.parse(fs.readFileSync(file, 'utf8'));
    editable.preferences = [];
    fs.writeFileSync(file, JSON.stringify(editable));
    assert.equal(readPreferences(file).length, 0);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});
