document.addEventListener('DOMContentLoaded', () => {
  const tabList = document.querySelector('.tabs');
  const panelsContainer = document.querySelector('.tabpanels');
  if (!tabList || !panelsContainer) return;

  // collect tab-panel pairs
  const tabs = Array.from(tabList.querySelectorAll('.tab'));
  const pairs = tabs.map(tab => {
    const panelId = tab.getAttribute('aria-controls');
    const panel = document.getElementById(panelId);
    return { tab, panel };
  });

  // shuffle pairs (Fisher–Yates)
  for (let i = pairs.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pairs[i], pairs[j]] = [pairs[j], pairs[i]];
  }

  // reinsert and set first active
  tabList.innerHTML = '';
  panelsContainer.innerHTML = '';
  pairs.forEach(({ tab, panel }, idx) => {
    const active = idx === 0;
    tab.setAttribute('aria-selected', active);
    panel.setAttribute('aria-hidden', !active);
    tabList.appendChild(tab);
    panelsContainer.appendChild(panel);
  });

  // interaction
  const allTabs = Array.from(document.querySelectorAll('.tab'));
  function activateTab(tab){
    allTabs.forEach(t => {
      const selected = t === tab;
      t.setAttribute('aria-selected', selected);
      const panel = document.getElementById(t.getAttribute('aria-controls'));
      panel.setAttribute('aria-hidden', !selected);
    });
    tab.focus();
  }

  allTabs.forEach(tab => {
    tab.addEventListener('click', () => activateTab(tab));
    tab.addEventListener('keydown', e => {
      const idx = allTabs.indexOf(tab);
      if (e.key === 'ArrowRight') { e.preventDefault(); activateTab(allTabs[(idx+1)%allTabs.length]); }
      if (e.key === 'ArrowLeft')  { e.preventDefault(); activateTab(allTabs[(idx-1+allTabs.length)%allTabs.length]); }
      if (e.key === 'Home')       { e.preventDefault(); activateTab(allTabs[0]); }
      if (e.key === 'End')        { e.preventDefault(); activateTab(allTabs[allTabs.length-1]); }
    });
  });
});
