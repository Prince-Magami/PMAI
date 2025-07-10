// chat.js - Handles all interactivity on the chat page

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const modeSelect = document.getElementById("mode-select");
const langToggle = document.getElementById("lang-toggle");
const sendButton = document.getElementById("send-button");

let currentMode = "chatbox";
let currentLang = "english";

// Handle mode change
modeSelect.addEventListener("change", (e) => {
  currentMode = e.target.value;
});

// Handle language toggle
langToggle.addEventListener("change", (e) => {
  currentLang = e.target.value;
});

// Handle form submit
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;
  addMessage("user", message);
  chatInput.value = "";
  await fetchReply(message);
});

// Allow Enter to send and Shift+Enter for newline
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendButton.click();
  }
});

// Fetch AI response
async function fetchReply(message) {
  addMessage("assistant", "<span class='typing'>Typing...</span>");
  try {
    const res = await fetch("https://pmai-api.onrender.com/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, mode: currentMode, lang: currentLang }),
    });
    const data = await res.json();
    updateLastAssistantMessage(data.reply || "An error occurred.");
  } catch (err) {
    updateLastAssistantMessage("Failed to get response. Please try again.");
  }
}

// Add message bubble
function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `chat-bubble ${role}`;
  wrapper.innerHTML = `<div class="message">${text}</div>`;
  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Update assistant's last message
function updateLastAssistantMessage(text) {
  const lastMsg = document.querySelector(".chat-bubble.assistant:last-child .message");
  if (lastMsg) lastMsg.innerHTML = text;
}
