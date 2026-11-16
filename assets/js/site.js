(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, r = document) => r.querySelector(s);

  /* ---------- clock (Tehran) ---------- */
  const clock = $('#clock');
  const fmt = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Tehran', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  const tick = () => { clock.textContent = fmt.format(new Date()); };
  tick(); setInterval(tick, 1000);
  $('#yr').textContent = new Date().getFullYear();

  /* ---------- reveal on scroll ---------- */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { rootMargin: '0px 0px -8% 0px' });
  document.querySelectorAll('.rv').forEach(el => io.observe(el));

  /* ---------- vision panel ---------- */
  const cv = $('#vision');
  if (cv) {
    const ctx = cv.getContext('2d');
    const W = cv.width, CELL = 7, N = Math.floor(W / CELL);
    const S = W / 550; // source image is 550px
    const face = { x: 165, y: 118, w: 222, h: 296 };
    const marks = [[222, 248], [325, 248], [275, 298], [246, 336], [304, 336]];
    const bayer = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map(v => (v + .5) / 16);
    const css = getComputedStyle(document.documentElement);
    const PAPER = css.getPropertyValue('--paper').trim(), SIG = css.getPropertyValue('--sig').trim();
    let cells = null, img = new Image(), mouse = null, t0 = performance.now(), frame = 0, visible = true;

    img.onload = () => {
      try {
        const o = document.createElement('canvas'); o.width = o.height = N;
        const oc = o.getContext('2d'); oc.drawImage(img, 0, 0, N, N);
        const d = oc.getImageData(0, 0, N, N).data;
        cells = [];
        for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
          const i = (y * N + x) * 4, r = d[i], g = d[i + 1], b = d[i + 2];
          const lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
          const warm = r > 190 && g < 150 && b < 110;
          if (1 - lum > 0.07 + bayer[(y % 4) * 4 + (x % 4)] * 0.8) cells.push([x, y, warm, 1 - lum]);
        }
      } catch (e) { cells = []; }
      loop();
    };
    img.src = '/assets/img/avatar.png';

    const bracket = (x, y, w, h, l) => {
      ctx.beginPath();
      ctx.moveTo(x, y + l); ctx.lineTo(x, y); ctx.lineTo(x + l, y);
      ctx.moveTo(x + w - l, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + l);
      ctx.moveTo(x + w, y + h - l); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - l, y + h);
      ctx.moveTo(x + l, y + h); ctx.lineTo(x, y + h); ctx.lineTo(x, y + h - l);
      ctx.stroke();
    };

    const draw = now => {
      const t = ((now - t0) / 1000) % 6;           // 6s cycle
      const scanY = Math.min(t / 2.2, 1) * W;       // scan in first 2.2s
      const found = t > 1.4;
      ctx.clearRect(0, 0, W, W);

      // dither field
      if (cells) for (const [x, y, warm, a] of cells) {
        const py = y * CELL;
        const lit = Math.abs(py - scanY) < 18 && t < 2.3;
        ctx.globalAlpha = lit ? 1 : 0.35 + a * 0.55;
        ctx.fillStyle = warm ? SIG : PAPER;
        const s = lit ? 4 : 2.6;
        ctx.fillRect(x * CELL + (CELL - s) / 2, py + (CELL - s) / 2, s, s);
      }
      ctx.globalAlpha = 1;

      // scan line
      if (t < 2.3) {
        ctx.fillStyle = SIG; ctx.globalAlpha = .9; ctx.fillRect(0, scanY, W, 1);
        ctx.globalAlpha = .08; ctx.fillRect(0, scanY - 40, W, 40); ctx.globalAlpha = 1;
      }

      // detection
      if (found) {
        const k = Math.min((t - 1.4) / .5, 1);
        const j = reduce ? 0 : Math.sin(now / 90) * 0.8;
        const x = face.x * S + j, y = face.y * S - j, w = face.w * S, h = face.h * S;
        ctx.strokeStyle = SIG; ctx.lineWidth = 1.5; ctx.globalAlpha = k;
        bracket(x, y, w, h, 18);
        ctx.lineWidth = 1; ctx.globalAlpha = k * .25; ctx.strokeRect(x, y, w, h); ctx.globalAlpha = k;
        const conf = (0.987 * k).toFixed(3);
        ctx.fillStyle = SIG; ctx.fillRect(x - 0.75, y - 22, 118, 20);
        ctx.fillStyle = '#0c0c0b'; ctx.font = '500 12px "IBM Plex Mono", monospace';
        ctx.fillText('face  ' + conf, x + 7, y - 8);
        $('#v-conf').textContent = conf;
        if (t > 1.9) marks.forEach(([mx, my], i) => {
          const a = Math.min((t - 1.9 - i * .08) / .3, 1); if (a <= 0) return;
          ctx.globalAlpha = a; ctx.strokeStyle = SIG; ctx.lineWidth = 1;
          const px = mx * S, py = my * S;
          ctx.beginPath(); ctx.moveTo(px - 6, py); ctx.lineTo(px + 6, py); ctx.moveTo(px, py - 6); ctx.lineTo(px, py + 6); ctx.stroke();
        });
        ctx.globalAlpha = 1;
      } else $('#v-conf').textContent = '0.000';

      // lens: raw pixels under cursor
      if (mouse && img.complete) {
        ctx.save(); ctx.beginPath(); ctx.arc(mouse.x, mouse.y, 74, 0, Math.PI * 2); ctx.clip();
        ctx.drawImage(img, 0, 0, W, W); ctx.restore();
        ctx.strokeStyle = PAPER; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(mouse.x, mouse.y, 74, 0, Math.PI * 2); ctx.stroke();
      }

      frame++;
      $('#v-frame').textContent = 'FRAME ' + String(frame % 10000).padStart(4, '0');
    };

    const loop = now => {
      if (visible) draw(now || performance.now());
      if (!reduce) requestAnimationFrame(loop);
    };
    if (reduce) t0 = performance.now() - 4000;

    new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(cv);
    const pos = e => { const r = cv.getBoundingClientRect(); const p = e.touches ? e.touches[0] : e; mouse = { x: (p.clientX - r.left) * W / r.width, y: (p.clientY - r.top) * W / r.height }; $('#v-hint').style.opacity = 0; if (reduce) draw(performance.now()); };
    cv.addEventListener('mousemove', pos);
    cv.addEventListener('mouseleave', () => { mouse = null; if (reduce) draw(performance.now()); });
  }

  /* ---------- ticket pipeline ---------- */
  const flow = $('#flow');
  if (flow) {
    const nodes = [...flow.querySelectorAll('.node')], packet = $('#packet'), log = $('#log'), count = $('#p-count');
    const tickets = [
      ['رمز عبور پنلم را فراموش کرده‌ام', 1, .94], ['فاکتور اسفند برایم ارسال نشده', 1, .91],
      ['چطور کاربر جدید به تیم اضافه کنم؟', 1, .96], ['خطای ۵۰۲ هنگام آپلود فایل بزرگ', 0, .58],
      ['امکان تغییر پلن اشتراک وسط ماه هست؟', 1, .89], ['درخواست بازگشت وجه سفارش', 0, .44],
      ['API کلید جدید چطور ساخته می‌شود؟', 1, .93], ['گزارش ماهانه خالی نمایش داده می‌شود', 1, .82]
    ];
    let id = 4810, ti = 0, step = 0;
    const place = i => { const n = nodes[i]; packet.style.left = (n.offsetLeft + n.offsetWidth / 2 - 3.5) + 'px'; };
    const push = (html) => {
      const r = document.createElement('div'); r.className = 'r'; r.innerHTML = html; log.appendChild(r);
      while (log.children.length > 4) log.firstChild.remove();
    };
    const esc = s => s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]);
    const run = () => {
      nodes.forEach((n, i) => n.classList.toggle('on', i === step));
      place(step);
      if (step === 0) { id++; count.textContent = '#' + id; }
      if (step === 3) {
        const [txt, ok, c] = tickets[ti++ % tickets.length];
        const ms = (0.9 + Math.random() * 1.1).toFixed(1);
        push(`<span>#${id}</span><span class="t">${esc(txt)}</span><span class="${ok ? 'ok' : 'sig'}">${ok ? '✓ resolved' : '↗ human'}</span><span>${ms}s · ${c.toFixed(2)}</span>`);
      }
      step = (step + 1) % 4;
    };
    for (let k = 0; k < 3; k++) { const [txt, ok, c] = tickets[ti++]; id++; push(`<span>#${id}</span><span class="t">${esc(txt)}</span><span class="${ok ? 'ok' : 'sig'}">${ok ? '✓ resolved' : '↗ human'}</span><span>${(1 + k * .3).toFixed(1)}s · ${c.toFixed(2)}</span>`); }
    run();
    if (!reduce) setInterval(run, 900);
    addEventListener('resize', () => place((step + 3) % 4));
  }

  /* ---------- similarity matrix ---------- */
  const mx = $('#matrix');
  if (mx) {
    const cells = Array.from({ length: 24 * 7 }, () => mx.appendChild(document.createElement('span')));
    const paint = () => cells.forEach((c, i) => {
      const diag = (i % 24) % 7 === Math.floor(i / 24);
      const r = Math.random();
      c.className = diag && r > .25 ? 'h2' : r > .9 ? 'h1' : '';
    });
    paint(); if (!reduce) setInterval(paint, 1400);
  }

  /* ---------- article: numbered headings, TOC, reading progress ---------- */
  const prose = $('.prose');
  if (prose) {
    const fa = n => String(n).padStart(2, '0');
    const hs = [...prose.querySelectorAll('h2')];
    const toc = $('#toc');
    hs.forEach((h, i) => {
      if (!h.id) h.id = 's' + (i + 1);
      h.insertAdjacentHTML('afterbegin', `<span class="hn">${fa(i + 1)}</span>`);
      if (toc) {
        const a = document.createElement('a'); a.href = '#' + h.id;
        a.textContent = h.textContent.replace(/^\d+/, '').trim();
        const li = document.createElement('li'); li.appendChild(a); toc.appendChild(li);
      }
    });
    if (toc) {
      const links = [...toc.querySelectorAll('a')];
      const spy = new IntersectionObserver(es => es.forEach(e => {
        if (e.isIntersecting) links.forEach(l => l.classList.toggle('on', l.hash === '#' + e.target.id));
      }), { rootMargin: '-20% 0px -70% 0px' });
      hs.forEach(h => spy.observe(h));
    }
    const bar = $('.progress i');
    if (bar) {
      const upd = () => {
        const r = prose.getBoundingClientRect();
        const p = Math.min(Math.max(-r.top / (r.height - innerHeight * .6), 0), 1);
        bar.style.transform = `scaleX(${p})`;
      };
      addEventListener('scroll', upd, { passive: true }); upd();
    }
  }

  /* ---------- blog index: tag filter ---------- */
  const filters = $('.filters');
  if (filters) {
    const posts = [...document.querySelectorAll('.posts .post')];
    const empty = $('.posts .empty');
    filters.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      filters.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b));
      const tag = b.dataset.tag; let n = 0;
      posts.forEach(p => { const show = tag === '*' || (p.dataset.tags || '').split(' ').includes(tag); p.hidden = !show; n += show; });
      if (empty) empty.hidden = n > 0;
    });
  }
})();
