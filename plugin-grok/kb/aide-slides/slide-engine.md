# Slide Engine — AIDE Slides

> The JavaScript engine and navigation chrome that powers every slide deck.

## SlideEngine Class

```javascript
class SlideEngine {
  constructor() {
    this.deck = document.getElementById('deck');
    this.slides = [...document.querySelectorAll('.slide')];
    this.dots = document.getElementById('dots');
    this.progress = document.getElementById('progress');
    this.counter = document.getElementById('counter');
    this.hints = document.getElementById('hints');
    this.total = this.slides.length;
    this.current = 0;

    // Create dot buttons
    this.slides.forEach((_, i) => {
      const d = document.createElement('button');
      d.className = 'deck-dot';
      d.setAttribute('aria-label', 'Ir para slide ' + (i + 1));
      d.addEventListener('click', () => this.goTo(i));
      this.dots.appendChild(d);
    });

    // Visibility observer — triggers reveal animations
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          this.current = this.slides.indexOf(e.target);
          this.updateChrome();
        }
      });
    }, { root: this.deck, threshold: 0.5 });
    this.slides.forEach(s => obs.observe(s));

    // Keyboard navigation
    document.addEventListener('keydown', e => {
      if (['ArrowDown','ArrowRight','Space','PageDown'].includes(e.code)) { e.preventDefault(); this.next(); }
      if (['ArrowUp','ArrowLeft','PageUp'].includes(e.code)) { e.preventDefault(); this.prev(); }
      if (e.code === 'Home') { e.preventDefault(); this.goTo(0); }
      if (e.code === 'End') { e.preventDefault(); this.goTo(this.total - 1); }
    });

    // Touch navigation (50px swipe threshold)
    let touchY = 0;
    this.deck.addEventListener('touchstart', e => { touchY = e.touches[0].clientY; }, { passive: true });
    this.deck.addEventListener('touchend', e => {
      const dy = touchY - e.changedTouches[0].clientY;
      if (Math.abs(dy) > 50) dy > 0 ? this.next() : this.prev();
    }, { passive: true });

    // Auto-fade hints after 4s
    setTimeout(() => this.hints.classList.add('faded'), 4000);
    this.updateChrome();
    if (this.slides[0]) this.slides[0].classList.add('visible');
  }

  goTo(i) { this.slides[i]?.scrollIntoView({ behavior: 'smooth' }); }
  next() { this.goTo(Math.min(this.current + 1, this.total - 1)); }
  prev() { this.goTo(Math.max(this.current - 1, 0)); }

  updateChrome() {
    const pct = ((this.current + 1) / this.total) * 100;
    this.progress.style.width = pct + '%';
    this.counter.textContent = (this.current + 1) + ' / ' + this.total;
    [...this.dots.children].forEach((d, i) => d.classList.toggle('active', i === this.current));
  }
}
new SlideEngine();
```

## Navigation Chrome HTML

```html
<div class="deck-progress" id="progress"></div>
<nav class="deck-dots" id="dots"></nav>
<div class="deck-counter" id="counter"></div>
<div class="deck-hints" id="hints">&larr; &rarr; ou scroll</div>
```

## Navigation Chrome CSS

```css
.deck-progress { position: fixed; top: 0; left: 0; height: 3px; background: linear-gradient(90deg, var(--accent), var(--gold)); z-index: 100; transition: width 0.3s ease; pointer-events: none; }
.deck-dots { position: fixed; right: clamp(12px,2vw,24px); top: 50%; transform: translateY(-50%); display: flex; flex-direction: column; gap: 7px; z-index: 100; padding: 7px; background: rgba(10,15,26,0.6); border-radius: 20px; backdrop-filter: blur(8px); }
.deck-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-dim); opacity: 0.3; border: none; padding: 0; cursor: pointer; transition: all 0.2s; }
.deck-dot:hover { opacity: 0.6; }
.deck-dot.active { opacity: 1; transform: scale(1.5); background: var(--accent); box-shadow: 0 0 8px rgba(0,180,255,0.4); }
.deck-counter { position: fixed; bottom: clamp(12px,2vh,24px); right: clamp(12px,2vw,24px); font-family: var(--font-mono); font-size: 12px; color: var(--text-dim); z-index: 100; }
.deck-hints { position: fixed; bottom: clamp(12px,2vh,24px); left: 50%; transform: translateX(-50%); font-family: var(--font-mono); font-size: 11px; color: var(--text-dim); opacity: 0.5; z-index: 100; transition: opacity 0.5s; }
.deck-hints.faded { opacity: 0; pointer-events: none; }
```

## Scroll-Snap Container

```css
.deck { height: 100dvh; overflow-y: auto; scroll-snap-type: y mandatory; scroll-behavior: smooth; position: relative; z-index: 1; }

.slide {
  height: 100dvh; scroll-snap-align: start; overflow: hidden; position: relative;
  display: flex; flex-direction: column; justify-content: center;
  padding: clamp(32px, 5vh, 64px) clamp(36px, 6vw, 96px);
  isolation: isolate; opacity: 0; transform: translateY(40px) scale(0.98);
  transition: opacity 0.6s cubic-bezier(0.16,1,0.3,1), transform 0.6s cubic-bezier(0.16,1,0.3,1);
}
.slide.visible { opacity: 1; transform: none; }
```

## Reveal Animation System

```css
.slide .reveal {
  opacity: 0; transform: translateY(24px);
  transition: opacity 0.5s cubic-bezier(0.16,1,0.3,1), transform 0.5s cubic-bezier(0.16,1,0.3,1);
}
.slide.visible .reveal { opacity: 1; transform: none; }
.slide.visible .reveal:nth-child(1) { transition-delay: 0.1s; }
.slide.visible .reveal:nth-child(2) { transition-delay: 0.2s; }
/* ... up to :nth-child(10) at 1.0s */
```
