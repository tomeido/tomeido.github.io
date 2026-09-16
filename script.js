(() => {
  const grid = document.getElementById('project-grid');
  const cards = Array.from(grid.querySelectorAll('.card'));
  const search = document.getElementById('project-search');
  const sort = document.getElementById('project-sort');
  const buttons = Array.from(document.querySelectorAll('.filter-btn[data-filter]'));
  const empty = document.getElementById('empty-state');
  const status = document.getElementById('filter-status');
  let category = 'all';
  const normalize = value => value.normalize('NFKC').toLocaleLowerCase();

  const searchable = new Map(cards.map(card => [card, normalize(card.textContent)]));

  function updateProjects() {
    const query = normalize(search.value.trim());
    let hasResults = false;
    const sorted = [...cards].sort((a, b) => {
      if (sort.value === 'recent') {
        const byDate = b.dataset.updated.localeCompare(a.dataset.updated);
        if (byDate) return byDate;
      }
      return a.dataset.name.localeCompare(b.dataset.name, 'en', { sensitivity: 'base' });
    });
    sorted.forEach(card => {
      const matches = (category === 'all' || card.dataset.cat === category)
        && searchable.get(card).includes(query);
      card.hidden = !matches;
      hasResults ||= matches;
      grid.appendChild(card);
    });
    buttons.forEach(button => {
      const active = button.dataset.filter === category;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    empty.hidden = hasResults;
    const label = buttons.find(button => button.dataset.filter === category).textContent;
    status.textContent = hasResults
      ? `${label} 프로젝트${query ? ` · “${search.value.trim()}” 검색 결과` : '를 표시합니다.'}`
      : '일치하는 프로젝트가 없습니다.';
  }

  search.addEventListener('input', updateProjects);
  sort.addEventListener('change', updateProjects);
  buttons.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.filter;
    updateProjects();
  }));
  document.getElementById('reset-filters').addEventListener('click', () => {
    search.value = '';
    category = 'all';
    updateProjects();
    search.focus();
  });
  updateProjects();
  document.querySelector('.project-toolbar').hidden = false;
  document.querySelector('.filters').hidden = false;
})();

// Decorative animation stays independent of project browsing.
(() => {
  const canvas = document.getElementById('bg-canvas');
  const context = canvas.getContext('2d');
  if (!context) return;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let width, height, particles = [], frame = null;

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    const count = Math.min(60, Math.floor(width * height / 14000));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * width, y: Math.random() * height,
      radius: Math.random() * 1.5 + 0.3,
      vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
      alpha: Math.random() * 0.4 + 0.05,
    }));
  }

  function draw() {
    context.clearRect(0, 0, width, height);
    for (const particle of particles) {
      particle.x = (particle.x + particle.vx + width) % width;
      particle.y = (particle.y + particle.vy + height) % height;
      context.beginPath();
      context.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
      context.fillStyle = `rgba(102,126,234,${particle.alpha})`;
      context.fill();
    }
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i], b = particles[j];
        const distance = Math.hypot(a.x - b.x, a.y - b.y);
        if (distance >= 120) continue;
        context.beginPath();
        context.strokeStyle = `rgba(102,126,234,${0.06 * (1 - distance / 120)})`;
        context.lineWidth = 0.5;
        context.moveTo(a.x, a.y);
        context.lineTo(b.x, b.y);
        context.stroke();
      }
    }
    frame = requestAnimationFrame(draw);
  }

  function updateAnimation() {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
    context.clearRect(0, 0, width, height);
    if (!reducedMotion.matches && !document.hidden) draw();
  }

  window.addEventListener('resize', resize);
  document.addEventListener('visibilitychange', updateAnimation);
  reducedMotion.addEventListener('change', updateAnimation);
  resize();
  updateAnimation();
})();
