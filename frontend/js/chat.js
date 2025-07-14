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

  // Simulate flashcard text from A.I
  function generateFlashcardText(mode) {
    const samples = {
      edu: [
        "🧠 Study in 25-min sessions with 5-min breaks (Pomodoro Technique).",
        "📚 Avoid cramming the night before your exam.",
        "📖 Teach someone else — it helps you retain better.",
        "📝 Make use of past questions and self-quizzing.",
        "📵 Turn off phone notifications during study time."
      ],
      cyber: [
        "🔐 Enable Two-Factor Authentication (2FA) on all important accounts.",
        "📛 Never click on unknown links in emails — phishing alert!",
        "💻 Use strong, unique passwords and a password manager.",
        "🕵️ Beware of social engineering. Always verify before trusting.",
        "🧼 Keep your software and antivirus updated regularly."
      ]
    };

    const chosen = samples[mode];
    const randomIndex = Math.floor(Math.random() * chosen.length);
    return chosen[randomIndex];
  }

  function showFlashcards(mode) {
    flashcardsContainer.innerHTML = "";
    flashcardSection.style.display = "block";

    // Show 3 unique cards
    const shown = new Set();
    while (shown.size < 3) {
      let text = generateFlashcardText(mode);
      if (!shown.has(text)) {
        const card = document.createElement('div');
        card.className = 'flashcard';
        card.textContent = text;
        flashcardsContainer.appendChild(card);
        shown.add(text);
      }
    }

    // Toggle study resources if mode is edu
    eduLinksContainer.style.display = mode === 'edu' ? 'block' : 'none';
  }

  function hideFlashcards() {
    flashcardSection.style.display = 'none';
  }

  // Update placeholder based on selected mode
  function updatePlaceholder() {
    const mode = modeSelect.value;

    if (mode === 'scan') {
      chatInput.placeholder = "Paste link or email here...";
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

  // Hide flashcards when user wants to type
  chatInput.addEventListener('focus', () => {
    hideFlashcards();
  });

  // Form Submission Handler
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
      const reply = data.reply || "⚠️ No response from AI.";

      appendMessage('bot', reply);
    } catch (err) {
      console.error("Error from API:", err);
      appendMessage('bot', '❌ Something went wrong. Please try again.');
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

  chatInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event('submit'));
    }
  });
});
