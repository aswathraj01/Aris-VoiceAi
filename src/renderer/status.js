const labels = {
  idle: ['Microphone off', 'Enable “Microphone wake word” from the tray'],
  armed: ['Wake word on', 'Say “ARIS” or “Hey ARIS” to start a request'],
  listening: ['Listening', 'Wake word heard. Say your request.'],
  thinking: ['Thinking', 'Processing on this computer'],
  working: ['Working', 'Running an approved task'],
  speaking: ['Speaking', 'Responding to you'],
  paused: ['Paused', 'Voice service needs attention']
};

const statusNode = document.getElementById('status');
const detailNode = document.getElementById('detail');
const messageNode = document.getElementById('message');
const panel = document.querySelector('.panel');

function renderStatus(status) {
  const [label, detail] = labels[status] || labels.idle;
  statusNode.textContent = label;
  if (!detailNode.dataset.custom) detailNode.textContent = detail;
  panel.dataset.state = status;
}

function renderDetail(detail) {
  detailNode.dataset.custom = 'true';
  detailNode.textContent = String(detail || '').slice(0, 110);
}

function renderMessage(message) {
  messageNode.textContent = String(message || '').slice(0, 180);
  messageNode.hidden = !message;
}

window.aris.getStatus().then(renderStatus).catch(() => renderStatus('idle'));
window.aris.getDetail().then(renderDetail).catch(() => {});
window.aris.onStatus(renderStatus);
window.aris.onDetail(renderDetail);
window.aris.onMessage(renderMessage);
