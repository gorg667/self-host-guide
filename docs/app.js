/* The Self-Hosting & Home Lab Guide — client script (no dependencies) */
(function () {
  'use strict';
  const ROOT = window.__ROOT__ || '';
  const $ = (s, el) => (el || document).querySelector(s);
  const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));

  /* ---- Theme ---- */
  const themeBtn = $('#themeBtn');
  function setTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    try { localStorage.setItem('theme', t); } catch (e) {}
  }
  themeBtn && themeBtn.addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme');
    setTheme(cur === 'dark' ? 'light' : 'dark');
  });

  /* ---- Mobile sidebar ---- */
  const sidebar = $('#sidebar');
  const menuBtn = $('#menuBtn');
  menuBtn && menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', (e) => {
    if (sidebar && sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== menuBtn) {
      sidebar.classList.remove('open');
    }
  });
  // scroll active chapter into view in the sidebar
  const active = $('.sidebar li.active');
  if (active && sidebar) {
    const r = active.getBoundingClientRect();
    if (r.top > window.innerHeight - 80) sidebar.scrollTop = active.offsetTop - 200;
  }

  /* ---- Fix the MD link path relative to root ---- */
  const mdLink = $('[data-md-link]');
  if (mdLink) {
    // On GitHub Pages the .md lives in the repo, not the site. Point at the GitHub blob view.
    mdLink.href = 'https://github.com/gorg667/self-host-guide/blob/main/SELF-HOSTING-GUIDE.md';
    mdLink.target = '_blank'; mdLink.rel = 'noopener';
  }

  /* ---- Copy buttons on code blocks ---- */
  $$('.prose pre').forEach((pre) => {
    if (pre.classList.contains('mermaid')) return;
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.textContent = 'Copy';
    btn.addEventListener('click', () => {
      const code = pre.querySelector('code') || pre;
      navigator.clipboard.writeText(code.innerText).then(() => {
        btn.textContent = 'Copied';
        setTimeout(() => (btn.textContent = 'Copy'), 1400);
      });
    });
    const host = pre.parentElement && pre.parentElement.classList.contains('highlight') ? pre.parentElement : pre;
    host.style.position = 'relative';
    host.appendChild(btn);
  });

  /* ---- Wrap tables for horizontal scroll ---- */
  $$('.prose table').forEach((t) => {
    if (t.parentElement.classList.contains('table-wrap')) return;
    const w = document.createElement('div');
    w.className = 'table-wrap';
    t.parentNode.insertBefore(w, t);
    w.appendChild(t);
  });

  /* ---- TOC scroll spy ---- */
  const tocLinks = $$('.toc-aside a[href^="#"]');
  if (tocLinks.length) {
    const map = new Map();
    tocLinks.forEach((a) => {
      const id = decodeURIComponent(a.getAttribute('href').slice(1));
      const el = document.getElementById(id);
      if (el) map.set(el, a);
    });
    const headings = Array.from(map.keys());
    let current = null;
    function onScroll() {
      const y = window.scrollY + 90;
      let best = null;
      for (const h of headings) { if (h.offsetTop <= y) best = h; else break; }
      if (best !== current) {
        current = best;
        tocLinks.forEach((a) => a.classList.remove('active'));
        if (best) {
          const a = map.get(best);
          a.classList.add('active');
          const tocBox = $('.toc-aside');
          if (tocBox) {
            const ar = a.getBoundingClientRect(), tr = tocBox.getBoundingClientRect();
            if (ar.top < tr.top + 40 || ar.bottom > tr.bottom - 40) a.scrollIntoView({ block: 'center' });
          }
        }
      }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---- Back to top ---- */
  const backTop = $('#backTop');
  if (backTop) {
    window.addEventListener('scroll', () => { backTop.hidden = window.scrollY < 600; }, { passive: true });
    backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  /* ---- Search ---- */
  const input = $('#search');
  const results = $('#searchResults');
  let index = null, loading = null, sel = -1;

  function loadIndex() {
    if (index) return Promise.resolve(index);
    if (!loading) {
      loading = fetch(ROOT + 'search-index.json').then((r) => r.json()).then((d) => {
        index = d.map((e) => ({ ...e, lc: (e.c + ' ' + e.h + ' ' + e.t).toLowerCase(), hl: e.h.toLowerCase(), cl: e.c.toLowerCase() }));
        return index;
      });
    }
    return loading;
  }
  function esc(s) { return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
  function mark(text, terms) {
    let out = esc(text);
    terms.forEach((t) => {
      if (!t) return;
      const re = new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig');
      out = out.replace(re, '<mark>$1</mark>');
    });
    return out;
  }
  function snippet(text, terms) {
    const lc = text.toLowerCase();
    let pos = -1;
    for (const t of terms) { pos = lc.indexOf(t); if (pos >= 0) break; }
    if (pos < 0) return text.slice(0, 140);
    const start = Math.max(0, pos - 60);
    return (start > 0 ? '…' : '') + text.slice(start, start + 160) + (start + 160 < text.length ? '…' : '');
  }
  function search(q) {
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    const scored = [];
    for (const e of index) {
      let score = 0, ok = true;
      for (const t of terms) {
        if (!e.lc.includes(t)) { ok = false; break; }
        if (e.hl.includes(t)) score += 10;
        if (e.cl.includes(t)) score += 4;
        if (e.hl === t) score += 20;
        score += 1;
      }
      if (ok) scored.push([score, e]);
    }
    scored.sort((a, b) => b[0] - a[0]);
    return scored.slice(0, 20).map((x) => x[1]).map((e) => ({ e, terms }));
  }
  function render(items) {
    sel = -1;
    if (!items.length) { results.innerHTML = '<div class="r-empty">No results.</div>'; results.hidden = false; return; }
    results.innerHTML = items.map(({ e, terms }) =>
      `<a href="${ROOT}${e.u}"><div class="r-ch">${esc(e.c)}</div><div class="r-h">${mark(e.h, terms)}</div><div class="r-t">${mark(snippet(e.t, terms), terms)}</div></a>`
    ).join('');
    results.hidden = false;
  }
  if (input && results) {
    let timer;
    input.addEventListener('input', () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) { results.hidden = true; return; }
      timer = setTimeout(() => loadIndex().then(() => render(search(q))), 80);
    });
    input.addEventListener('focus', () => loadIndex());
    input.addEventListener('keydown', (e) => {
      const links = $$('a', results);
      if (e.key === 'ArrowDown') { e.preventDefault(); sel = Math.min(links.length - 1, sel + 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(0, sel - 1); }
      else if (e.key === 'Enter') { if (sel >= 0 && links[sel]) location.href = links[sel].href; return; }
      else if (e.key === 'Escape') { results.hidden = true; input.blur(); return; }
      else return;
      links.forEach((l, i) => l.classList.toggle('sel', i === sel));
      if (links[sel]) links[sel].scrollIntoView({ block: 'nearest' });
    });
    document.addEventListener('click', (e) => { if (!results.contains(e.target) && e.target !== input) results.hidden = true; });
    document.addEventListener('keydown', (e) => {
      if (e.key === '/' && document.activeElement !== input && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
        e.preventDefault(); input.focus();
      }
    });
  }
})();
