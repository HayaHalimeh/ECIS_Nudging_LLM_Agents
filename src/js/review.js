document.addEventListener('DOMContentLoaded', () => {
  const data = JSON.parse(localStorage.getItem('upbSelections') || '[]');
  const root = document.getElementById('review-root');

  if (!data.length) {
    root.innerHTML = "<p>Keine Auswahl gefunden. <a href='index.html'>Zurück zum Shop</a>.</p>";
    return;
  }

  root.innerHTML = data.map(cat => {
    const [o1, o2] = cat.options;
    const c1 = cat.selectedValue === (o1?.value || '');
    const c2 = cat.selectedValue === (o2?.value || '');
    return `
      <section class="category" data-key="${cat.categoryKey}">
        <div class="category-title">${cat.categoryTitle}</div>
        <div class="row">
          ${[o1, o2].map((o, idx) => o ? `
            <label class="card">
              <span class="choice">
                <input type="radio" name="${cat.categoryKey}" value="${o.value}" 
                  ${idx===0 && c1 ? 'checked' : ''} 
                  ${idx===1 && c2 ? 'checked' : ''}/>
                <span>${o.title}</span>
              </span>
              <span class="imgwrap"><img src="${o.img}" alt="${o.title}"></span>
            </label>
          ` : '').join('')}
        </div>
      </section>
    `;
  }).join('');

  // update storage when user changes a choice
  root.addEventListener('change', (e) => {
    if (!e.target.matches('input[type="radio"]')) return;
    const section = e.target.closest('.category');
    const key = section.getAttribute('data-key');
    const value = e.target.value;
    const idx = data.findIndex(c => c.categoryKey === key);
    if (idx !== -1) {
      data[idx].selectedValue = value;
      localStorage.setItem('upbSelections', JSON.stringify(data));
    }
  });

  // nav buttons
  document.getElementById('backBtn').addEventListener('click', () => history.back());
  document.getElementById('nextBtn').addEventListener('click', async () => {
    // Save current selections to server before moving on.
    try {
      const payload = data || JSON.parse(localStorage.getItem('upbSelections') || '[]');
      const resp = await fetch('/api/save_selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || 'Save failed');
      }
      const json = await resp.json();
      console.info('Saved selection:', json);
      // Proceed to final page
      window.location.href = './end.html';
    } catch (err) {
      console.error('Error saving selection', err);
      alert('Fehler beim Speichern Ihrer Auswahl. Bitte versuchen Sie es erneut.');
    }
  });
});
