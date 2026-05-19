# Template — AIDE Slides

> The complete HTML skeleton for starting a new slide deck. Copy this and fill in the slides.

## Full Template

Replace `{{LESSON_CODE}}`, `{{LESSON_TITLE}}`, `{{LESSON_SUBTITLE}}`, `{{MODULE_NUM}}`, `{{MODULE_NAME}}`, `{{DURATION}}` with actual values.

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{LESSON_CODE}} — {{LESSON_TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@400;500;600;700;800&family=Fira+Code:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400;1,6..72,500&display=swap" rel="stylesheet">
<style>
  /* Paste full CSS from design-system.md + component-library.md + animation-patterns.md */
  /* See those KB files for the complete CSS */
</style>
</head>
<body>

<!-- AIDE BRANDING BAR -->
<div class="aide-bar">
  <div class="aide-bar__left">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
    FORMAÇÃO AI DATA ENGINEER
  </div>
  <div class="aide-bar__center">De AI-Curious a AI-Native Engineer</div>
  <div class="aide-bar__right">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
    Luan Moreno &middot; 2026
  </div>
</div>

<!-- NAV CHROME -->
<div class="deck-progress" id="progress"></div>
<nav class="deck-dots" id="dots"></nav>
<div class="deck-counter" id="counter"></div>
<div class="deck-hints" id="hints">&larr; &rarr; ou scroll</div>

<div class="deck" id="deck">

<!-- SLIDE 1 — TITLE -->
<section class="slide slide--title">
  <svg class="slide__decor" style="top:0;left:0;" width="200" height="200" viewBox="0 0 200 200">
    <line x1="0" y1="0" x2="0" y2="60" stroke="var(--accent)" stroke-width="2" opacity="0.15"/>
    <line x1="0" y1="0" x2="60" y2="0" stroke="var(--accent)" stroke-width="2" opacity="0.15"/>
  </svg>
  <svg class="slide__decor" style="bottom:0;right:0;" width="200" height="200" viewBox="0 0 200 200">
    <line x1="200" y1="140" x2="200" y2="200" stroke="var(--gold)" stroke-width="2" opacity="0.15"/>
    <line x1="140" y1="200" x2="200" y2="200" stroke="var(--gold)" stroke-width="2" opacity="0.15"/>
  </svg>
  <div class="reveal">
    <p class="slide__subtitle" style="margin-bottom:clamp(4px,1vh,8px); letter-spacing:3px; font-size:0.72rem;">MÓDULO {{MODULE_NUM}} &mdash; {{MODULE_NAME}}</p>
  </div>
  <div class="reveal" style="margin-bottom:clamp(8px,1.5vh,16px);">
    <span class="tag tag-accent" style="font-size:0.82rem; padding:0.4rem 1.2rem; border-radius:100px;">{{LESSON_CODE}}</span>
    <span class="tag tag-gold" style="font-size:0.72rem; padding:0.3rem 0.8rem; border-radius:100px; margin-left:0.5rem;">{{DURATION}}</span>
  </div>
  <h1 class="slide__display reveal" style="font-size:clamp(40px,8vw,100px);">{{LESSON_TITLE_LINE1}}<br><span class="shimmer-text">{{LESSON_TITLE_LINE2}}</span></h1>
  <div class="reveal" style="margin-top:clamp(12px,2vh,20px);">
    <p style="font-family:var(--font-editorial); font-size:clamp(20px,3vw,34px); font-style:italic; color:var(--text-dim);">{{LESSON_SUBTITLE}}</p>
  </div>
  <div class="reveal" style="margin-top:clamp(20px,3vh,32px); display:flex; align-items:center; justify-content:center; gap:clamp(12px,2vw,20px);">
    <div style="width:clamp(56px,7vw,80px); height:clamp(56px,7vw,80px); border-radius:50%; overflow:hidden; border:2px solid rgba(0,180,255,0.3); flex-shrink:0;">
      <img src="../../../images/luan-moreno.png" alt="Luan Moreno" style="width:100%; height:100%; object-fit:cover; object-position:center -5%; transform:scale(1.3); transform-origin:center 3%;">
    </div>
    <div style="text-align:left;">
      <p style="font-family:var(--font-display); font-size:1.2rem; font-style:italic;"><span style="color:var(--text-dim);">Instrutor:</span> <span style="color:var(--accent);">Luan Moreno</span></p>
      <p style="font-family:var(--font-mono); font-size:0.62rem; color:var(--text-dim); letter-spacing:0.12em; margin-top:0.2rem;">AIDE BRASIL &middot; aide-brasil.ai</p>
    </div>
  </div>
  <div class="reveal" style="margin-top:clamp(12px,2vh,20px); display:flex; gap:0.75rem; justify-content:center; flex-wrap:wrap;">
    <span class="tag tag-purple">Layer 1 &middot; Foundations</span>
    <span class="tag tag-cyan">Self-Paced</span>
    <span class="tag tag-gold">aide-brasil.ai</span>
  </div>
</section>

<!-- ADD CONTENT SLIDES HERE -->
<!-- Use slide types from slide-types.md -->
<!-- Use components from component-library.md -->
<!-- Follow rules from quality-rules.md -->

<!-- CLOSING SLIDE -->
<section class="slide slide--quote">
  <div class="reveal"><div class="slide__quote-mark" style="color:var(--gold);">&ldquo;</div></div>
  <div class="reveal">
    <blockquote>{{CLOSING_QUOTE}}</blockquote>
  </div>
  <div class="reveal" style="margin-top:clamp(20px,3vh,32px); display:flex; gap:0.75rem; justify-content:center;">
    <span class="tag tag-accent" style="font-size:0.82rem; padding:0.4rem 1.2rem; border-radius:100px;">Próximo: {{NEXT_LESSON}}</span>
  </div>
  <div class="reveal" style="margin-top:clamp(24px,4vh,36px);">
    <p style="font-family:var(--font-mono); font-size:0.68rem; color:var(--text-dim); letter-spacing:0.15em;">FORMAÇÃO AI DATA ENGINEER · AIDE BRASIL · aide-brasil.ai · 2026</p>
  </div>
</section>

</div><!-- /deck -->

<script>
/* Paste SlideEngine from slide-engine.md */
</script>
</body>
</html>
```

## Checklist Before Generating

Before writing any HTML, verify:

- [ ] Read `quality-rules.md` — especially screen filling and accent rules
- [ ] Read lesson CSV row for: code, title, duration, hook, content, closing
- [ ] Read support doc for: talking points, exercises, evidence data
- [ ] Map every content item to a slide type (from `slide-types.md`)
- [ ] Plan 15-20 slides minimum for a 12-min lesson
- [ ] Every content slide has a bottom "why" panel
- [ ] Every card has a practical example
- [ ] All Portuguese text uses proper accents
