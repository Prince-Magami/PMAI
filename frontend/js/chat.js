document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatWindow = document.getElementById('chat-window');
  const modeSelect = document.getElementById('mode');
  const langSelect = document.getElementById('lang');
  const flashcardSection = document.getElementById('flashcard-section');
  const flashcardsContainer = document.getElementById('flashcards');
  const eduLinksContainer = document.getElementById('edu-links');

  const API_BASE = 'https://pmai-pm.onrender.com'; // ✅ Your FastAPI backend URL

  // 📚 Sample flashcard text
  function generateFlashcardText(mode) {
    const samples = {
      edu: [
        "🧠 Use spaced repetition to retain concepts longer.",
        "📚 Study with practice questions, not just notes.",
        "🎯 Set clear study goals before each session.",
        "☕ Avoid studying while tired or hungry.",
        "📵 Turn off distractions during focused study time."
      ],
      cyber: [
        "🔐 Use Two-Factor Authentication for all major accounts.",
        "🚫 Don’t share your OTP with anyone — ever!",
        "🔍 Inspect URLs carefully to avoid phishing traps.",
        "🧼 Keep all software and apps updated regularly.",
        "🔒 Use a password manager instead of reusing passwords."
      ]
    };

    const modeCards = samples[mode];
    const chosen = new Set();
    while (chosen.size < 3) {
      const card = modeCards[Math.floor(Math.random() * modeCards.length)];
      chosen.add(card);
    }

    return [...chosen];
  }

  // 🎴 Show Flashcards
  function showFlashcards(mode) {
    flashcardsContainer.innerHTML = '';
    flashcardSection.style.display = 'block';

    const flashcards = generateFlashcardText(mode);
    flashcards.forEach(text => {
      const card = document.createElement('div');
      card.className = 'flashcard';
      card.textContent = text;
      flashcardsContainer.appendChild(card);
    });

    eduLinksContainer.style.display = mode === 'edu' ? 'block' : 'none';
  }

  // 🙈 Hide Flashcards
  function hideFlashcards() {
    flashcardSection.style.display = 'none';
    eduLinksContainer.style.display = 'none';
  }

  // 🛠️ Mode change behavior
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
      chatInput.placeholder = "Type a message...";
      hideFlashcards();
    }
  }

  modeSelect.addEventListener('change', updatePlaceholder);
  updatePlaceholder();

  chatInput.addEventListener('focus', hideFlashcards);

  // ✉️ Submit message
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
      const reply = data.reply || "⚠️ No response from Gemini.";

      appendMessage('bot', reply);
    } catch (err) {
      console.error("Gemini API Error:", err);
      appendMessage('bot', '❌ Something went wrong. Try again.');
    } finally {
      chatInput.disabled = false;
      sendBtn.disabled = false;
      sendBtn.textContent = "Send";
      chatInput.focus();
    }
  });

  // 🗨️ Display message in chat window
  function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    msgDiv.textContent = text;
    chatWindow.appendChild(msgDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  // ⌨️ Enter to send (Shift+Enter = new line)
  chatInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event('submit'));
    }
  });
});
