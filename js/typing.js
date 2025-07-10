// typing.js - Typing animation for home or chatbot intro

document.addEventListener("DOMContentLoaded", () => {
  const animatedText = document.querySelectorAll(".typing-effect");

  animatedText.forEach(el => {
    const text = el.getAttribute("data-text");
    let index = 0;

    function typeLetter() {
      if (index < text.length) {
        el.textContent += text.charAt(index);
        index++;
        setTimeout(typeLetter, 60);
      }
    }

    el.textContent = "";
    typeLetter();
  });
});
