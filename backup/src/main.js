import './base.css';

/* ── Shared nav behaviour (runs on every page) ─── */
function initNav() {
  const nav = document.getElementById('siteNav');
  const menuBtn = document.getElementById('menuBtn');
  const closeBtn = document.getElementById('closeBtn');
  const mobileNav = document.getElementById('mobileNav');

  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 40);
    }, { passive: true });
  }

  if (menuBtn && closeBtn && mobileNav) {
    const closeMenu = () => {
      mobileNav.classList.remove('open');
      mobileNav.setAttribute('aria-hidden', 'true');
      closeBtn.classList.remove('open');
      menuBtn.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    };
    menuBtn.addEventListener('click', () => {
      mobileNav.classList.add('open');
      mobileNav.setAttribute('aria-hidden', 'false');
      closeBtn.classList.add('open');
      menuBtn.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    });
    closeBtn.addEventListener('click', closeMenu);
    mobileNav.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMenu));
  }
}

/* ── Fade-up observer (runs on every page) ──────── */
function initFadeUp() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: .08, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
}

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initFadeUp();
});
