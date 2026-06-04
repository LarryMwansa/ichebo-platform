// Nav scroll — adds .scrolled class after 40px
const nav = document.getElementById('siteNav');
if (nav) {
  // Pages that need always-dark nav set data-always-dark on the <nav>
  if (nav.dataset.alwaysDark !== undefined) {
    nav.classList.add('scrolled');
  }
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  }, { passive: true });
}

// Mobile menu
const menuBtn = document.getElementById('menuBtn');
const closeBtn = document.getElementById('closeBtn');
const mobileNav = document.getElementById('mobileNav');

if (menuBtn && closeBtn && mobileNav) {
  menuBtn.addEventListener('click', () => {
    mobileNav.classList.add('open');
    mobileNav.setAttribute('aria-hidden', 'false');
    closeBtn.classList.add('open');
    menuBtn.classList.add('open');
    document.body.style.overflow = 'hidden';
  });

  closeBtn.addEventListener('click', () => {
    mobileNav.classList.remove('open');
    mobileNav.setAttribute('aria-hidden', 'true');
    closeBtn.classList.remove('open');
    menuBtn.classList.remove('open');
    document.body.style.overflow = '';
  });
}

// Fade-up scroll animations
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      observer.unobserve(e.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
