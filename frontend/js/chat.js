document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatWindow = document.getElementById('chat-window');
  const modeSelect = document.getElementById('mode');
  const langSelect = document.getElementById('lang');
  const flashcardSection = document.getElementById('flashcard-section');
  const flashcardsContainer = document.getElementById('flashcards');
  const eduLinksContainer = document.getElementById('edu-links');

  const API_BASE = 'https://pmai-pm.onrender.com';

  async function fetchFlashcards(mode) {
    try {
      const res = await fetch(`${API_BASE}/api/flashcards?mode=${mode}`);
      const data = await res.json();
      return data.flashcards || [];
    } catch (err) {
      console.error("Flashcard Error:", err);
      return [];
    }
  }

  async function showFlashcards(mode) {
    const flashcards = await fetchFlashcards(mode);
    if (flashcards.length === 0) return;

    flashcardsContainer.innerHTML = "";
    flashcards.forEach(text => {
      const card = document.createElement("div");
      card.className = "flashcard";
      card.textContent = text;
      flashcardsContainer.appendChild(card);
    });

    flashcardSection.style.display = "block";
    eduLinksContainer.style.display = mode === "edu" ? "block" : "none";
  }

  function hideFlashcards() {
    flashcardSection.style.display = "none";
    eduLinksContainer.style.display = "none";
  }

  function updatePlaceholder() {
    const mode = modeSelect.value;

    if (mode === 'scan') {
      chatInput.placeholder = "Paste link or email here...";
      hideFlashcards();
    } else if (mode === 'edu') {
      chatInput.placeholder = "Ask an academic-related question...";
      showFlashcards('edu');
    } else if (mode === 'cyber') {
      chatInput.placeholder = "Ask a cybersecurity question...";
      showFlashcards('cyber');
    } else {
      chatInput.placeholder = "Type something...";
      hideFlashcards();
    }
  }

  modeSelect.addEventListener('change', updatePlaceholder);
  updatePlaceholder();

  chatInput.addEventListener('focus', hideFlashcards);

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = chatInput.value.trim();
    if (!input) return;

    const mode = modeSelect.value;
    const lang = langSelect.value;

    appendMessage('user', input);
    chatInput.value = '';
    chatInput.disabled = true;

    const sendBtn = chatForm.querySelector('button');
    sendBtn.disabled = true;
    sendBtn.textContent = "Thinking...";

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, mode, lang })
      });

      if (!res.ok) throw new Error("Response not OK");

      const data = await res.json();
      let reply = data.reply || "No response from AI.";

      
      if (mode === 'scan') {
        reply = formatScannerReply(reply);
      }

      appendMessage('bot', reply);
    } catch (err) {
      console.error("Error from API:", err);
      appendMessage('bot', ' Something went wrong. Try again.');
    } finally {
      chatInput.disabled = false;
      sendBtn.disabled = false;
      sendBtn.textContent = "Send";
      chatInput.focus();
    }
  });

  function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    msgDiv.textContent = text;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  function formatScannerReply(rawText) {
    const percentMatch = rawText.match(/(\d+)%/);
    const risk = percentMatch ? parseInt(percentMatch[1]) : null;
    if (risk !== null) {
      return `Trust Score: ${risk}%\n Analysis: ${rawText}`;
    } else {
      return ` ${rawText}`;
    }
  }

  chatInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event('submit'));
    }
  });
});
