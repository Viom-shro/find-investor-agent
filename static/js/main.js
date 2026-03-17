document.addEventListener('DOMContentLoaded', () => {
  const queryInput = document.getElementById('queryInput');
  const searchBtn  = document.getElementById('searchBtn');
  const resultsList = document.getElementById('resultsList');
  const stats       = document.getElementById('stats');
  const loading     = document.getElementById('loading');

  searchBtn.addEventListener('click', performSearch);

  // Optional: search on Enter key
  queryInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
  });

  async function performSearch() {
    const query = queryInput.value.trim();
    if (!query) return;

    // Reset UI
    resultsList.innerHTML = '';
    stats.textContent = '';
    loading.classList.remove('hidden');

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });

      if (!response.ok) throw new Error('Server error');

      const data = await response.json();

      loading.classList.add('hidden');

      if (data.investors && data.investors.length > 0) {
        stats.textContent = `Found ${data.investors.length} matching investors`;
        if (data.message) stats.textContent += ` — ${data.message}`;
        renderInvestors(data.investors);
      } else {
        stats.textContent = data.message || 'No investors found for this query.';
      }
    } catch (err) {
      loading.classList.add('hidden');
      stats.textContent = 'Something went wrong. Try again.';
      console.error(err);
    }
  }

  function renderInvestors(investors) {
    investors.forEach(inv => {
      const card = document.createElement('div');
      card.className = 'investor-card';

      card.innerHTML = `
        <h3>${inv.name || 'Investor / Firm'}</h3>
        <div class="meta">${inv.location || ''} ${inv.type ? `• ${inv.type}` : ''}</div>
        <div class="focus">Focus: ${inv.focus || '—'}</div>
        ${inv.check_size ? `<div class="amount">Check size: ${inv.check_size}</div>` : ''}
      `;

      resultsList.appendChild(card);
    });
  }
});