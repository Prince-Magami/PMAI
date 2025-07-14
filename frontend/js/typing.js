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


window.addEventListener("DOMContentLoaded", () => {
  fadeInOnScroll();
  smoothScrollSetup();

  const heroText = document.getElementById("hero-text");
  if (heroText) {
    typeWriterEffect("Prince Magami AI (PMAI) - Your Intelligent Assistant", "hero-text", 75);
  }
});
