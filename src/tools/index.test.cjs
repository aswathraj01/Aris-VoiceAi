const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { parseLocalRequest, runLocalRequest, searchFileNames } = require('./index.cjs');

test('parses only the supported local actions', () => {
  assert.deepEqual(parseLocalRequest('Can you open Chrome?'), { name: 'openChrome' });
  assert.deepEqual(parseLocalRequest('please open Gmail'), { name: 'openGmail' });
  assert.deepEqual(parseLocalRequest('find the file named invoice'), { name: 'searchFiles', query: 'invoice' });
  assert.equal(parseLocalRequest('run this powershell command'), null);
  assert.equal(parseLocalRequest('open Photoshop'), null);
});

test('searches filenames inside approved roots without reading file contents', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aris-search-'));
  try {
    fs.mkdirSync(path.join(root, 'nested'));
    fs.writeFileSync(path.join(root, 'nested', 'invoice-2026.txt'), 'unrelated body');
    fs.writeFileSync(path.join(root, 'notes.txt'), 'invoice appears only inside this file');
    const result = await searchFileNames('invoice', [root]);
    assert.deepEqual(result.matches.map((item) => item.name), ['invoice-2026.txt']);
    assert.equal(result.matches[0].path, path.join(root, 'nested', 'invoice-2026.txt'));
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('rejects drive roots and has a useful empty-allowlist response', async () => {
  const result = await runLocalRequest({ name: 'searchFiles', query: 'tax' }, { approvedRoots: [] });
  assert.match(result.text, /No search folders are approved/);
  assert.equal(result.action, 'searchFiles');
});

test('launches only the preselected Chrome action without a shell', async () => {
  let captured;
  const launched = await runLocalRequest({ name: 'openGmail' }, {
    launchChrome: async (url, options) => {
      captured = { url, options };
    }
  });
  assert.equal(captured.url, 'https://mail.google.com/');
  assert.equal(launched.action, 'openGmail');
  assert.match(launched.text, /Gmail/);
});
