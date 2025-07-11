// ===========================
// chat.js - Frontend logic
// ===========================

const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatWindow = document.getElementById('chat-window');
const modeSelect = document.getElementById('mode');
const langSelect = document.getElementById('lang');

// Update placeholder based on selected mode
function updatePlaceholder() {
  const mode = modeSelect.value;
  if (mode === 'scan') {
    chatInput.placeholder = "Paste link or email here...";
  } else if (mode === 'edu') {
    chatInput.placeholder = "Ask an academic-related question...";
  } else if (mode === 'cyber') {
    chatInput.placeholder = "Ask a cybersecurity question...";
  } else {
    chatInput.placeholder = "Type something...";
  }
}

modeSelect.addEventListener('change', updatePlaceholder);

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const input = chatInput.value.trim();
  if (!input) return;

  const mode = modeSelect.value;
  const lang = langSelect.value;

  // Add user message
  appendMessage('user', input);
  chatInput.value = '';

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: input, mode, lang })
    });

    const data = await res.json();
    appendMessage('bot', data.response);

  } catch (err) {
    appendMessage('bot', '⚠️ Something went wrong. Please try again.');
  }
});

function appendMessage(sender, text) {
  const msgDiv = document.createElement('div');
  msgDiv.classList.add('message', sender);
  msgDiv.textContent = text;
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Allow enter to send, shift+enter for newline
chatInput.addEventListener("keydown", function(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event('submit'));
  }
});

// Initial placeholder load
updatePlaceholder();
