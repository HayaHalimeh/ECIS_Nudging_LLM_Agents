function getCategoryTitleByPanelId(panelId){
  const tab = document.querySelector(`.tabs .tab[aria-controls="${panelId}"]`);
  return tab ? tab.textContent.trim() : panelId.replace(/^panel-/, "");
}
// ✅ save logic for checkout page
function collectCatalogAndSelection(){
  const panels = Array.from(document.querySelectorAll('.tabpanel'));
  return panels.map(panel => {
    const categoryKey = panel.id;
    const categoryTitle = getCategoryTitleByPanelId(panel.id);
    const options = Array.from(panel.querySelectorAll('label.option')).map(opt => {
      const r = opt.querySelector('input[type="radio"]');
      return {
        value: r?.value || '',
        title: opt.querySelector('.title')?.textContent.trim() || '',
        img: opt.querySelector('img')?.getAttribute('src') || ''
      };
    });
    const selectedInput = panel.querySelector('input[type="radio"]:checked');
    return { categoryKey, categoryTitle, options, selectedValue: selectedInput ? selectedInput.value : null };
  });
}

document.addEventListener('DOMContentLoaded', () => {

  // ✅ RANDOMIZE product order in each category
  const optionGroups = document.querySelectorAll('.options');
  optionGroups.forEach(group => {
    const labels = Array.from(group.querySelectorAll('label.option'));
    // Fisher–Yates shuffle
    for (let i = labels.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [labels[i], labels[j]] = [labels[j], labels[i]];
    }
    labels.forEach(label => group.appendChild(label));
  });

  // ✅ Existing checkout button logic
  const btn = document.getElementById('checkout-btn') || document.querySelector('.checkout-btn');
  if (!btn) return;

  btn.addEventListener('click', () => {
    if (btn.disabled) return; // skip if validation fails

    // Save the current selections
    localStorage.setItem('upbSelections', JSON.stringify(collectCatalogAndSelection()));

    // Redirect to the review page
    window.location.href = './review.html';
  });
});
