// landing.js

const title = document.getElementById("pmai-title");
const subtitle = document.getElementById("pmai-subtitle");

const typingDelay = 100;
const modes = ["Chatbox", "Email/Link Scanner", "Academic Assistant", "Cybersecurity Tips"];

function typeEffect(element, text, delay = typingDelay) {
  let i = 0;
  function type() {
    if (i < text.length) {
      element.textContent += text.charAt(i);
      i++;
      setTimeout(type, delay);
    }
  }
  type();
}

function loopModes() {
  let modeIndex = 0;
  function updateSubtitle() {
    subtitle.textContent = "";
    typeEffect(subtitle, modes[modeIndex]);
    modeIndex = (modeIndex + 1) % modes.length;
    setTimeout(updateSubtitle, 3000);
  }
  updateSubtitle();
}

typeEffect(title, "PMAI");
loopModes();
