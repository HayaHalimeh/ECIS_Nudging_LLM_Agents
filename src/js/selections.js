function validateSelections() {
  const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
  const groups = [...new Set(radios.map(r => r.name))];
  const allChosen = groups.every(name => !!document.querySelector(`input[name="${name}"]:checked`));
  const alertBox = document.getElementById('no-selection');
  if (alertBox) alertBox.classList.toggle('d-none', allChosen);

  // toggle checkout enabled/disabled
  const btn = document.getElementById('checkout-btn');
  if (btn) btn.disabled = !allChosen;
}

document.addEventListener('change', (e) => {
  if (e.target.matches('input[type="radio"]')) validateSelections();
});

document.addEventListener('DOMContentLoaded', validateSelections);
