const labels = {
  idle: ['Ready', 'Voice input is not connected yet'],
  listening: ['Listening', 'Voice input is active'],
  thinking: ['Thinking', 'Preparing a response'],
  working: ['Working', 'Running an approved task'],
  speaking: ['Speaking', 'Responding to you'],
  paused: ['Paused', 'ARIS is waiting']
};

const statusNode = document.getElementById('status');
const detailNode = document.getElementById('detail');
const panel = document.querySelector('.panel');

function render(status) {
  const [label, detail] = labels[status] || labels.idle;
  statusNode.textContent = label;
  detailNode.textContent = detail;
  panel.dataset.state = status;
}

window.aris.getStatus().then(render).catch(() => render('idle'));
window.aris.onStatus(render);
