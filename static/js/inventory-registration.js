(() => {
  'use strict';
  const form = document.getElementById('inventory-registration');
  if (!form) return;
  const field = name => form.elements.namedItem(name);
  // Fracciones con BigInt: la vista previa tampoco depende de coma flotante.
  function decimal(value) {
    const match = /^(\d+)(?:[.,](\d+))?$/.exec(String(value).trim());
    if (!match) return null;
    const decimals = match[2] || '';
    return {n: BigInt(match[1] + decimals), d: 10n ** BigInt(decimals.length)};
  }
  const divide = (a, b) => b && b.n > 0n ? {n: a.n * b.d, d: a.d * b.n} : null;
  const multiply = (a, b) => ({n: a.n * b.n, d: a.d * b.d});
  function format(value) {
    if (!value) return '—';
    const scale = 100000000n;
    const rounded = (value.n * scale * 2n + value.d) / (2n * value.d);
    let fraction = String(rounded % scale).padStart(8, '0').replace(/0+$/, '');
    const integer = String(rounded / scale).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return integer + (fraction ? `,${fraction}` : '');
  }
  function display(id, value) {
    const output = document.getElementById(id);
    if (output) output.textContent = value ? `$${format(value)}` : '—';
  }
  function update() {
    const unit = field('base_unit').value;
    const divisible = unit !== 'UNIT';
    const symbol = unit === 'ML' ? 'ml' : unit === 'G' ? 'g' : 'unidades';
    ['content', 'usage_price'].forEach(name => {
      const wrapper = form.querySelector(`[data-field="${name}"]`);
      if (wrapper) wrapper.hidden = !divisible;
      field(name).disabled = !divisible || (name === 'content' && field(name).dataset.locked === 'true');
    });
    form.querySelectorAll('[data-divisible]').forEach(node => { node.hidden = !divisible; });
    form.querySelectorAll('[data-unit]').forEach(node => { node.textContent = symbol; });
    const minimumLabel = form.querySelector('label[for="id_minimum_stock"]');
    if (minimumLabel) minimumLabel.textContent = `Stock mínimo (${symbol}) *`;
    const minimumHelp = form.querySelector('[data-field="minimum_stock"] .text-xs');
    if (minimumHelp) minimumHelp.textContent = `Se expresa en ${symbol}${divisible ? ', no en presentaciones completas.' : '.'}`;
    const content = divisible ? decimal(field('content').value) : {n: 1n, d: 1n};
    const sale = decimal(field('presentation_sale_price').value);
    const count = field('presentation_count') ? decimal(field('presentation_count').value) : null;
    const total = field('total_cost') ? decimal(field('total_cost').value) : null;
    const proportional = content && sale ? divide(sale, content) : null;
    const cost = count && total ? divide(total, count) : null;
    display('preview-package-cost', cost);
    display('preview-unit-cost', cost && content ? divide(cost, content) : null);
    display('preview-proportional', proportional);
    display('preview-usage', field('usage_price').value.trim() ? decimal(field('usage_price').value) : proportional);
    const quantity = document.getElementById('preview-quantity');
    if (quantity) quantity.textContent = count && content && count.n > 0n && content.n > 0n ? `${format(multiply(count, content))} ${symbol}` : '—';
    const hint = document.getElementById('preview-hint');
    hint.textContent = proportional && (form.dataset.mode === 'edit' || cost) ? 'Valores calculados automáticamente con los datos del formulario.' : 'Completa cantidades, costo total y precio de venta para ver los valores calculados.';
  }
  form.addEventListener('input', update);
  form.addEventListener('change', update);
  form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Guardando…';
  });
  update();
})();
