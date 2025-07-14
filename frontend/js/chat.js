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

  // Static flashcards for immediate display
  const staticFlashcards = {
    edu: [
      "Break study time into chunks (Pomodoro).",
      "Test yourself regularly with past questions.",
      "🗂Make summary notes while reading.",
      "Minimize distractions when studying.",
      "Write what you remember after learning."
    ],
    cyber: [
      "Use 2FA to protect your accounts.",
      "Don’t click suspicious links or attachments.",
      "Update your antivirus and OS regularly.",
      "Learn to spot phishing emails.",
      "Avoid using public Wi-Fi for banking."
    ]
  };

  // Fetch AI-generated flashcards
  async function fetchFlashcards(mode) {
    try {
      const res = await fetch(`${API_BASE}/api/flashcards?mode=${mode}`);
      const data = await res.json();
      return data.flashcards || [];
    } catch (err) {
      console.error("Flashcard fetch error:", err);
      return [];
    }
  }

  async function showFlashcards(mode) {
    flashcardsContainer.innerHTML = "";
    flashcardSection.style.display = "block";
    eduLinksContainer.style.display = mode === "edu" ? "block" : "none";

    // Show 3 static cards immediately
    const picked = new Set();
    while (picked.size < 3) {
      const card = staticFlashcards[mode][Math.floor(Math.random() * staticFlashcards[mode].length)];
      if (!picked.has(card)) {
        const div = document.createElement('div');
        div.className = "flashcard";
        div.textContent = card;
        flashcardsContainer.appendChild(div);
        picked.add(card);
      }
    }

    // Replace with AI flashcards 
    setTimeout(async () => {
      const aiCards = await fetchFlashcards(mode);
      if (!aiCards.length) return;
      flashcardsContainer.innerHTML = "";
      aiCards.forEach(text => {
        const div = document.createElement("div");
        div.className = "flashcard";
        div.textContent = text;
        flashcardsContainer.appendChild(div);
      });
    }, 2000);
  }

  // Hide flashcards & resources
  function hideFlashcards() {
    flashcardSection.style.display = "none";
    eduLinksContainer.style.display = "none";
  }

  // Update input placeholder and flashcard visibility
  function updatePlaceholder() {
    const mode = modeSelect.value;
    if (mode === 'scan') {
      chatInput.placeholder = "Paste link or email here...";
      hideFlashcards();
    } else if (mode === 'edu') {
      chatInput.placeholder = "Ask an academic-related question...";
      showFlashcards("edu");
    } else if (mode === 'cyber') {
      chatInput.placeholder = "Ask a cybersecurity question...";
      showFlashcards("cyber");
    } else {
      chatInput.placeholder = "Type something...";
      hideFlashcards();
    }
  }

  modeSelect.addEventListener("change", updatePlaceholder);
  updatePlaceholder();

  chatInput.addEventListener("focus", hideFlashcards);

  // Handle message submit
  chatForm.addEventListener("submit", async (e) => {
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

      if (mode === 'scan') reply = formatScannerReply(reply);

      appendMessage('bot', reply);
    } catch (err) {
      console.error("Error from API:", err);
      appendMessage('bot', 'Something went wrong. Try again.');
    } finally {
      chatInput.disabled = false;
      sendBtn.disabled = false;
      sendBtn.textContent = "Send";
      chatInput.focus();
    }
  });

  // Add message to chat window
  function appendMessage(sender, text) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.textContent = text;
    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  // Format scan results if % present
  function formatScannerReply(text) {
    const match = text.match(/(\d+)%/);
    const score = match ? parseInt(match[1]) : null;
    return score ? `Trust Score: ${score}%\nAnalysis: ${text}` : text;
  }

  // Allow Enter to send
  chatInput.addEventListener("keydown",
