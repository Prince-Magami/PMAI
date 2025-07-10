// typing.js
// 🧠 Handles typing animation and auto-scroll for PMAI chat UI

document.addEventListener("DOMContentLoaded", () => {
  const chatWindow = document.getElementById("chat-window");

  // Typing animation effect for AI reply
  function typeText(element, text, callback) {
    let i = 0;
    const speed = 20; // typing speed in ms
    function type() {
      if (i < text.length) {
        element.innerHTML += text.charAt(i);
        i++;
        chatWindow.scrollTop = chatWindow.scrollHeight;
        setTimeout(type, speed);
      } else if (callback) {
        callback();
      }
    }
    type();
  }

  // Append message to chat window
  window.appendChatMessage = function (sender, message) {
    const wrapper = document.createElement("div");
    wrapper.className = `message ${sender}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    if (sender === "ai") {
      typeText(bubble, message);
    } else {
      bubble.textContent = message;
    }

    wrapper.appendChild(bubble);
    chatWindow.appendChild(wrapper);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  };
});
