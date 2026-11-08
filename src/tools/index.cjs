const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');

const MAX_DEPTH = 8;
const MAX_ENTRIES = 5000;
const MAX_RESULTS = 15;
const SKIP_DIRS = new Set(['.git', 'node_modules', 'appdata', 'windows', '$recycle.bin', 'system volume information']);

function parseLocalRequest(input) {
  const text = String(input || '').trim().replace(/[.!?]+$/, '');
  const prefix = '(?:(?:hey\\s+(?:aris|eris|iris)[, ]*)?(?:please\\s+)?(?:can you\\s+)?)?';
  if (new RegExp('^' + prefix + '(?:open|launch|go to|search)\\s+(?:the\\s+)?youtube(?:\\.com)?$', 'i').test(text)) {
    return { name: 'openYouTube' };
  }
  const youtubeSearch = text.match(new RegExp('^' + prefix + '(?:search(?:\\s+on)?|look up|find)\\s+(?:on\\s+)?youtube\\s+(?:(?:for|about)\\s+)?(.+)$', 'i'));
  if (youtubeSearch) {
    const query = youtubeSearch[1].trim().replace(/^['\"]|['\"]$/g, '').slice(0, 160);
    if (query) return { name: 'searchYouTube', query };
  }
  const firstVideo = text.match(new RegExp('^' + prefix + '(?:open|play)(?:\\s+me)?\\s+(?:the\\s+)?first\\s+(?:video|result|one)(?:\\s+for\\s+(.+))?$', 'i'));
  const betterVideo = new RegExp('^' + prefix + '(?:find|open|play)\\s+(?:me\\s+)?(?:a\\s+)?better\\s+video$', 'i').test(text);
  if (firstVideo || betterVideo) {
    const query = firstVideo && firstVideo[1] ? firstVideo[1].trim().replace(/^['\"]|['\"]$/g, '').slice(0, 160) : '';
    return { name: 'openFirstYouTubeResult', ...(query ? { query } : {}) };
  }
  if (new RegExp('^' + prefix + '(?:open|launch|start)\\s+(?:(?:google\\s+)?chrome)(?:\\s+browser)?$', 'i').test(text)) {
    return { name: 'openChrome' };
  }
  if (new RegExp('^' + prefix + '(?:open|launch)\\s+(?:(?:my|google)\\s+)?(?:gmail|email|mail)$', 'i').test(text)) {
    return { name: 'openGmail' };
  }
  const fileSearch = text.match(new RegExp('^' + prefix + '(?:find|search for|look for)\\s+(?:(?:the|a)\\s+)?file(?:\\s+(?:named|called))?\\s+(.+)$', 'i'));
  if (fileSearch) {
    const query = fileSearch[1].trim().replace(/^['\"]|['\"]$/g, '').slice(0, 100);
    if (query) return { name: 'searchFiles', query };
  }
  return null;
}

function approvedRootsFromFile(filePath) {
  try {
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    return Array.isArray(data.roots) ? data.roots.filter((item) => typeof item === 'string') : [];
  } catch {
    return [];
  }
}

function normalizeRoots(roots) {
  const valid = [];
  for (const root of Array.isArray(roots) ? roots : []) {
    if (typeof root !== 'string' || !root.trim() || root.startsWith('\\\\')) continue;
    const resolved = path.resolve(root);
    if (path.parse(resolved).root.toLowerCase() === resolved.toLowerCase()) continue;
    try {
      const stat = fs.lstatSync(resolved);
      if (stat.isDirectory() && !stat.isSymbolicLink()) valid.push(fs.realpathSync(resolved));
    } catch {}
  }
  return [...new Set(valid)];
}

async function searchFileNames(query, roots, options = {}) {
  const needle = String(query || '').trim().toLocaleLowerCase();
  if (!needle) return { matches: [], scanned: 0, truncated: false };
  const maxDepth = options.maxDepth ?? MAX_DEPTH;
  const maxEntries = options.maxEntries ?? MAX_ENTRIES;
  const maxResults = options.maxResults ?? MAX_RESULTS;
  const matches = [];
  const stack = normalizeRoots(roots).map((root) => ({ dir: root, depth: 0 }));
  let scanned = 0;

  while (stack.length > 0 && scanned < maxEntries && matches.length < maxResults) {
    const current = stack.pop();
    let entries;
    try {
      entries = await fs.promises.readdir(current.dir, { withFileTypes: true });
    } catch {
      continue;
    }

    for (const entry of entries) {
      if (scanned >= maxEntries || matches.length >= maxResults) break;
      scanned += 1;
      if (entry.isSymbolicLink()) continue;
      const fullPath = path.join(current.dir, entry.name);
      if (entry.isFile() && entry.name.toLocaleLowerCase().includes(needle)) {
        matches.push({ name: entry.name, path: fullPath });
      } else if (entry.isDirectory() && current.depth < maxDepth && !SKIP_DIRS.has(entry.name.toLocaleLowerCase())) {
        stack.push({ dir: fullPath, depth: current.depth + 1 });
      }
    }
  }
  return { matches, scanned, truncated: stack.length > 0 || scanned >= maxEntries };
}

function extractFirstYouTubeVideoId(html) {
  const content = String(html || '');
  const match = content.match(/"videoRenderer":\s*\{\s*"videoId":"([A-Za-z0-9_-]{11})"/) || content.match(/"videoId":"([A-Za-z0-9_-]{11})"/);
  return match ? match[1] : null;
}

function chromeCandidates(env = process.env) {
  const roots = [env.PROGRAMFILES, env['PROGRAMFILES(X86)'], env.LOCALAPPDATA].filter(Boolean);
  return roots.map((root) => path.join(root, 'Google', 'Chrome', 'Application', 'chrome.exe'));
}

function resolveChromeExecutable(env = process.env) {
  return chromeCandidates(env).find((candidate) => fs.existsSync(candidate)) || null;
}

function launchChrome(url, options = {}) {
  const env = options.env || process.env;
  const spawnImpl = options.spawnImpl || spawn;
  const executable = resolveChromeExecutable(env);
  if (!executable) return Promise.reject(new Error('Google Chrome was not found on this computer.'));
  const args = url ? [url] : ['--new-window'];
  return new Promise((resolve, reject) => {
    const child = spawnImpl(executable, args, { detached: true, windowsHide: true, stdio: 'ignore' });
    child.once('error', reject);
    child.once('spawn', () => { child.unref(); resolve(); });
  });
}

async function runLocalRequest(request, options = {}) {
  if (!request) return null;
  if (request.name === 'openChrome') {
    await (options.launchChrome || launchChrome)(null, options);
    return { action: request.name, text: 'Chrome is open.' };
  }
  if (request.name === 'openYouTube') {
    await (options.launchChrome || launchChrome)('https://www.youtube.com/', options);
    return { action: request.name, text: 'YouTube is open. Tell me what to search for.' };
  }
  if (request.name === 'searchYouTube') {
    const query = String(request.query || '').trim().slice(0, 160);
    if (!query) return { action: request.name, text: 'Tell me what you want to search for on YouTube.' };
    const url = 'https://www.youtube.com/results?search_query=' + encodeURIComponent(query);
    await (options.launchChrome || launchChrome)(url, options);
    return { action: request.name, text: 'I searched YouTube for ' + query + '. Say “open the first video” to play the top result.' };
  }
  if (request.name === 'openFirstYouTubeResult') {
    const query = String(request.query || options.lastYouTubeSearchQuery || '').trim().slice(0, 160);
    if (!query) return { action: request.name, text: 'What should I search for on YouTube first?' };
    const searchUrl = 'https://www.youtube.com/results?search_query=' + encodeURIComponent(query);
    try {
      const fetchImpl = options.fetchImpl || globalThis.fetch;
      const response = await fetchImpl(searchUrl, { signal: AbortSignal.timeout(12000), headers: { 'User-Agent': 'Mozilla/5.0 ARIS/0.1' } });
      if (!response.ok) throw new Error('YouTube search returned HTTP ' + response.status);
      const html = await response.text();
      const videoId = extractFirstYouTubeVideoId(html);
      if (!videoId) throw new Error('No video result found.');
      await (options.launchChrome || launchChrome)('https://www.youtube.com/watch?v=' + videoId, options);
      return { action: request.name, text: 'I opened the top YouTube result for ' + query + '.' };
    } catch {
      await (options.launchChrome || launchChrome)(searchUrl, options);
      return { action: request.name, text: 'I could not select the top result automatically, so I opened the YouTube results for ' + query + '.' };
    }
  }
  if (request.name === 'openGmail') {
    await (options.launchChrome || launchChrome)('https://mail.google.com/', options);
    return { action: request.name, text: 'I opened Gmail in Chrome.' };
  }
  if (request.name === 'searchFiles') {
    const roots = normalizeRoots(options.approvedRoots || []);
    if (roots.length === 0) {
      return { action: request.name, text: 'No search folders are approved yet. Add local folder paths to approved_roots.json, then ask me to search again.' };
    }
    const result = await searchFileNames(request.query, roots);
    if (result.matches.length === 0) return { action: request.name, text: 'I did not find a filename matching ' + request.query + '.' };
    const names = result.matches.slice(0, 5).map((match) => match.name);
    const suffix = result.matches.length > names.length || result.truncated ? ' There may be more matches.' : '';
    return { action: request.name, text: 'I found ' + names.join(', ') + '.' + suffix };
  }
  return null;
}

module.exports = { approvedRootsFromFile, extractFirstYouTubeVideoId, normalizeRoots, parseLocalRequest, resolveChromeExecutable, runLocalRequest, searchFileNames };
