(() => {
  'use strict';

  const search = document.getElementById('search');
  if (search) {
    const cards = [...document.querySelectorAll('.entry-card[data-search]')];
    const filters = [...document.querySelectorAll('button[data-type]')];
    const collection = document.getElementById('collection');
    const count = document.getElementById('results-count');
    const empty = document.getElementById('no-results');
    const params = new URLSearchParams(location.search);
    const normalize = value => value.toLocaleLowerCase().normalize('NFKD').replace(/\p{M}/gu, '');
    const haystacks = cards.map(card => normalize(card.dataset.search));
    const initialType = params.get('type');
    let type = filters.some(filter => filter.dataset.type === initialType) ? initialType : 'All';
    search.value = params.get('q') || '';
    if (Array.from(collection.options).some(option => option.value === params.get('set'))) {
      collection.value = params.get('set');
    }

    function applyFilters() {
      const term = search.value.trim();
      const words = normalize(term).split(/\s+/);
      let matches = 0;
      cards.forEach((card, index) => {
        const visible = (type === 'All' || type === card.dataset.type)
          && (collection.value === 'All' || collection.value === card.dataset.collection)
          && words.every(word => haystacks[index].includes(word));
        card.hidden = !visible;
        matches += Number(visible);
      });
      count.textContent = `Showing ${matches} of ${cards.length} packages`;
      empty.hidden = matches > 0;
      for (const filter of filters) {
        const selected = filter.dataset.type === type;
        filter.classList.toggle('active', selected);
        filter.setAttribute('aria-pressed', String(selected));
      }
      const state = new URLSearchParams();
      if (term) state.set('q', term);
      if (type !== 'All') state.set('type', type);
      if (collection.value !== 'All') state.set('set', collection.value);
      try {
        history.replaceState(null, '', location.pathname + (state.size ? '?' + state : '') + location.hash);
      } catch (_) {
        // Catalog filtering also works when the ZIP is opened from a local filesystem.
      }
    }

    search.addEventListener('input', applyFilters);
    collection.addEventListener('change', applyFilters);
    for (const filter of filters) {
      filter.addEventListener('click', () => {
        type = filter.dataset.type;
        applyFilters();
      });
    }
    document.getElementById('clear-search').addEventListener('click', () => {
      type = 'All';
      search.value = '';
      collection.value = 'All';
      applyFilters();
      search.focus();
    });
    document.addEventListener('keydown', event => {
      if (event.key === '/' && !event.target.closest('input,textarea,select,[contenteditable]')) {
        event.preventDefault();
        search.focus();
      }
    });
    applyFilters();
  }

  function selectForCopy(button) {
    const field = document.createElement('textarea');
    field.value = button.dataset.copy;
    field.readOnly = true;
    field.className = 'sr-only';
    document.body.append(field);
    field.select();
    try {
      return document.execCommand('copy');
    } finally {
      field.remove();
      button.focus();
    }
  }

  for (const button of document.querySelectorAll('button[data-copy]')) {
    const label = button.textContent;
    let timer;
    button.addEventListener('click', async () => {
      let copied = false;
      try {
        await navigator.clipboard.writeText(button.dataset.copy);
        copied = true;
      } catch (_) {
        copied = selectForCopy(button);
      }
      button.textContent = copied ? 'Copied' : 'Select the text to copy';
      clearTimeout(timer);
      timer = setTimeout(() => { button.textContent = label; }, 1700);
    });
  }
})();
