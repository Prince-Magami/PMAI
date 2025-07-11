// typing.js

// Typing effect for hero title or any element with class ".typewriter"
function typeWriterEffect(text, elementId, speed = 100) {
  let i = 0;
  const target = document.getElementById(elementId);
  function typing() {
    if (i < text.length) {
      target.innerHTML += text.charAt(i);
      i++;
      setTimeout(typing, speed);
    }
  }
  target.innerHTML = "";
  typing();
}

// Fade in on scroll
function fadeInOnScroll() {
  const elements = document.querySelectorAll(".fade-in");
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
      }
    });
  }, { threshold: 0.1 });

  elements.forEach((el) => observer.observe(el));
}

// Smooth scroll to sections
function smoothScrollSetup() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelector(this.getAttribute('href')).scrollIntoView({
        behavior: 'smooth'
      });
    });
  });
}

// Init all
window.addEventListener("DOMContentLoaded", () => {
  fadeInOnScroll();
  smoothScrollSetup();

  const heroText = document.getElementById("hero-text");
  if (heroText) {
    typeWriterEffect("Prince Magami AI (PMAI) - Your Intelligent Assistant", "hero-text", 75);
  }
});
