document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatWindow = document.getElementById('chat-window');
  const modeSelect = document.getElementById('mode');
  const langSelect = document.getElementById('lang');

  const API_BASE = 'https://pmai-3.onrender.com'; // ✅ Your deployed backend

  // 🔁 Update placeholder based on selected mode
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
  updatePlaceholder(); // 🔄 Initial run

  // 💬 Form Submission Handler
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const input = chatInput.value.trim();
    if (!input) return;

    const mode = modeSelect.value;
    const lang = langSelect.value;

    // 🧠 Show user message
    appendMessage('user', input);
    chatInput.value = '';

    // Disable input and button while waiting
    chatInput.disabled = true;
    const sendBtn = chatForm.querySelector('button');
    sendBtn.disabled = true;
    sendBtn.textContent = "Thinking...";

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: input, mode, lang })
      });

      if (!res.ok) throw new Error("Response not OK");

      const data = await res.json();
      const reply = data.response || "⚠️ No response from AI.";

      appendMessage('bot', reply);
    } catch (err) {
      console.error("❌ Error from API:", err);
      appendMessage('bot', '⚠️ Something went wrong. Please try again.');
    } finally {
      chatInput.disabled = false;
      sendBtn.disabled = false;
      sendBtn.textContent = "Send";
      chatInput.focus();
    }
  });

  // 💡 Append message to chat window
  function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    msgDiv.textContent = text;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  // ⌨️ Enter to send, Shift+Enter for new line
  chatInput.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event('submit'));
    }
  });
});
