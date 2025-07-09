// chat.js - Interactive JS for PMAI Chat Page

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatWindow = document.getElementById("chat-window");
const modeSelector = document.getElementById("mode-selector");
const langSelector = document.getElementById("lang-selector");

let currentMode = modeSelector.value;
let currentLang = langSelector.value;

modeSelector.addEventListener("change", () => {
  currentMode = modeSelector.value;
  displayTipForMode(currentMode);
});

langSelector.addEventListener("change", () => {
  currentLang = langSelector.value;
});

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendMessage("You", message);
  chatInput.value = "";
  chatInput.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        mode: currentMode,
        lang: currentLang,
      }),
    });

    const data = await response.json();
    appendMessage("PMAI", data.reply);
  } catch (err) {
    appendMessage("PMAI", "Error: Failed to connect to PMAI server.");
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});

function appendMessage(sender, text) {
  const bubble = document.createElement("div");
  bubble.classList.add("bubble", sender === "You" ? "user" : "ai");

  const label = document.createElement("div");
  label.classList.add("sender");
  label.textContent = sender;

  const message = document.createElement("div");
  message.classList.add("text");
  message.innerText = "";

  bubble.appendChild(label);
  bubble.appendChild(message);
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  // Typing animation
  let index = 0;
  const typing = setInterval(() => {
    if (index < text.length) {
      message.innerText += text.charAt(index);
      index++;
    } else {
      clearInterval(typing);
    }
  }, 20);
}

function displayTipForMode(mode) {
  if (mode === "cyber") {
    appendMessage("PMAI", "💡 Tip: Always use strong, unique passwords and enable 2FA.");
  } else if (mode === "scanner") {
    appendMessage("PMAI", "📌 Paste the email or URL you want to check for safety.");
  } else if (mode === "edu") {
    appendMessage("PMAI", "📚 Ask your academic questions or choose help type.");
  } else if (mode === "chat") {
    appendMessage("PMAI", "👋 I'm here to chat about anything!");
  } else if (mode === "advice") {
    appendMessage("PMAI", "🧠 I offer life advice. How can I help today?");
  }
}
