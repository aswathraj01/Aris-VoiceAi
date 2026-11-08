const fs = require('node:fs');
const path = require('node:path');
const MAX_PREFERENCES = 40;
const MAX_TEXT_LENGTH = 300;

function parsePreferenceRequest(input) {
  const text = String(input || '').trim().replace(/[.!?]+$/, '');
  const prefix = '(?:(?:hey\\s+aris[, ]*)?(?:please\\s+)?)?';
  if (new RegExp('^' + prefix + '(?:list|show)\\s+(?:my\\s+)?preferences$', 'i').test(text)) {
    return { action: 'list' };
  }
  const match = text.match(new RegExp('^' + prefix + 'remember(?:\\s+that)?\\s+(.+)$', 'i'));
  if (match) {
    const value = match[1].trim().slice(0, MAX_TEXT_LENGTH);
    if (value) return { action: 'remember', text: value };
  }
  return null;
}

function readPreferences(filePath) {
  try {
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    if (!Array.isArray(data.preferences)) return [];
    return data.preferences.filter((item) => item && typeof item.text === 'string' && item.text.trim())
      .slice(-MAX_PREFERENCES)
      .map((item) => ({ id: String(item.id || ''), text: item.text.trim().slice(0, MAX_TEXT_LENGTH), createdAt: String(item.createdAt || '') }));
  } catch { return []; }
}

function writePreferences(filePath, preferences) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify({ preferences: preferences.slice(-MAX_PREFERENCES) }, null, 2) + '\n', { mode: 0o600 });
}

function applyPreferenceRequest(filePath, request) {
  if (!request) return null;
  const current = readPreferences(filePath);
  if (request.action === 'remember') {
    const text = request.text.trim().slice(0, MAX_TEXT_LENGTH);
    if (!text) return { action: 'remember', text: 'I did not save an empty preference.' };
    if (!current.some((item) => item.text.toLocaleLowerCase() === text.toLocaleLowerCase())) {
      current.push({ id: Date.now().toString(36), text, createdAt: new Date().toISOString() });
      writePreferences(filePath, current);
    }
    return { action: 'remember', text: 'I’ll remember that preference. You can review or remove it from the tray menu.' };
  }
  if (request.action === 'list') {
    if (!current.length) return { action: 'listPreferences', text: 'You do not have any saved preferences yet.' };
    return { action: 'listPreferences', text: 'Your saved preferences are: ' + current.slice(0, 5).map((item) => item.text).join('. ') + (current.length > 5 ? '. You can review the rest from the tray menu.' : '') };
  }
  return null;
}

function preferenceContext(filePath) {
  return readPreferences(filePath).map((item) => '- ' + item.text).join('\n');
}

module.exports = { applyPreferenceRequest, parsePreferenceRequest, preferenceContext, readPreferences };
