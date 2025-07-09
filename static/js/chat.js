const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatLog = document.getElementById('chat-log');
const modeSelector = document.getElementById('mode');
const langSelector = document.getElementById('language');

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const userText = chatInput.value.trim();
  if (!userText) return;

  const userBubble = document.createElement('div');
  userBubble.classList.add('user-message');
  userBubble.textContent = userText;
  chatLog.appendChild(userBubble);
  chatLog.scrollTop = chatLog.scrollHeight;

  chatInput.value = '';

  const mode = modeSelector.value;
  const lang = langSelector.value;

  const responseBubble = document.createElement('div');
  responseBubble.classList.add('ai-message');
  responseBubble.textContent = 'Typing...';
  chatLog.appendChild(responseBubble);
  chatLog.scrollTop = chatLog.scrollHeight;

  try {
    const res = await fetch('https://your-api-endpoint.com/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userText, mode, lang })
    });

    const data = await res.json();
    responseBubble.textContent = data.reply;
  } catch (err) {
    responseBubble.textContent = 'Error fetching response.';
  }

  chatLog.scrollTop = chatLog.scrollHeight;
});
