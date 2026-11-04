(() => {
  'use strict';
  const integerFormatter = new Intl.NumberFormat('es-CO');
  const unitSymbols = {ML: 'ml', G: 'g', UNIT: 'unidades'};
  // Fracciones con BigInt: la vista previa tampoco depende de coma flotante.
  function decimal(value) {
    const match = /^(\d+)(?:[.,](\d+))?$/.exec(String(value).trim());
    if (!match) return null;
    const decimals = match[2] || '';
    return {n: BigInt(match[1] + decimals), d: 10n ** BigInt(decimals.length)};
  }
  function divide(a, b) {
    if (!a || !b || b.n <= 0n) return null;
    return {n: a.n * b.d, d: a.d * b.n};
  }
  const multiply = (a, b) => ({n: a.n * b.n, d: a.d * b.d});
  function format(value) {
    if (!value) return '—';
    const scale = 100000000n;
    const rounded = (value.n * scale * 2n + value.d) / (2n * value.d);
    let fraction = String(rounded % scale).padStart(8, '0');
    while (fraction.endsWith('0')) fraction = fraction.slice(0, -1);
    const integer = integerFormatter.format(rounded / scale);
    return integer + (fraction ? `,${fraction}` : '');
  }
  function setText(output, text) {
    if (output) output.textContent = text;
  }
  function display(document, id, value) {
    const output = document.getElementById(id);
    setText(output, value ? `$${format(value)}` : '—');
  }
  function readDecimalField(form, name) {
    const input = form.elements.namedItem(name);
    return decimal(input?.value ?? '');
  }
  function updateMeasurements(form, unit, symbol) {
    const divisible = unit !== 'UNIT';
    ['content', 'usage_price'].forEach(name => {
      const wrapper = form.querySelector(`[data-field="${name}"]`);
      if (wrapper) wrapper.hidden = !divisible;
      const input = form.elements.namedItem(name);
      input.disabled = !divisible || (name === 'content' && input.dataset.locked === 'true');
    });
    form.querySelectorAll('[data-divisible]').forEach(node => { node.hidden = !divisible; });
    form.querySelectorAll('[data-unit]').forEach(node => { node.textContent = symbol; });
    const minimumLabel = form.querySelector('label[for="id_minimum_stock"]');
    setText(minimumLabel, `Stock mínimo (${symbol}) *`);
    const minimumHelp = form.querySelector('[data-field="minimum_stock"] .text-xs');
    const suffix = divisible ? ', no en presentaciones completas.' : '.';
    setText(minimumHelp, `Se expresa en ${symbol}${suffix}`);
  }
  function readPreviewValues(form, unit) {
    const content = unit === 'UNIT' ? {n: 1n, d: 1n} : readDecimalField(form, 'content');
    const count = readDecimalField(form, 'presentation_count');
    const total = readDecimalField(form, 'total_cost');
    const sale = readDecimalField(form, 'presentation_sale_price');
    const proportional = divide(sale, content);
    const cost = divide(total, count);
    const usageText = form.elements.namedItem('usage_price').value.trim();
    const usage = usageText ? decimal(usageText) : proportional;
    return {content, count, proportional, cost, usage};
  }
  function formatQuantity(count, content, symbol) {
    if (!count || !content || count.n <= 0n || content.n <= 0n) return '—';
    return `${format(multiply(count, content))} ${symbol}`;
  }
  function renderPreview(document, form, values, symbol) {
    display(document, 'preview-package-cost', values.cost);
    display(document, 'preview-unit-cost', divide(values.cost, values.content));
    display(document, 'preview-proportional', values.proportional);
    display(document, 'preview-usage', values.usage);
    setText(document.getElementById('preview-quantity'), formatQuantity(values.count, values.content, symbol));
    const complete = values.proportional && (form.dataset.mode === 'edit' || values.cost);
    const hint = complete ? 'Valores calculados automáticamente con los datos del formulario.' : 'Completa cantidades, costo total y precio de venta para ver los valores calculados.';
    setText(document.getElementById('preview-hint'), hint);
  }
  function updatePreview(document, form) {
    const unit = form.elements.namedItem('base_unit').value;
    const symbol = unitSymbols[unit] ?? 'unidades';
    updateMeasurements(form, unit, symbol);
    renderPreview(document, form, readPreviewValues(form, unit), symbol);
  }
  function disableSubmit(form) {
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Guardando…';
  }
  function initializeInventoryRegistration(document) {
    const form = document.getElementById('inventory-registration');
    if (!form) return;
    const update = () => updatePreview(document, form);
    form.addEventListener('input', update);
    form.addEventListener('change', update);
    form.addEventListener('submit', () => disableSubmit(form));
    update();
  }
  if (typeof module !== 'undefined') {
    module.exports = {initializeInventoryRegistration};
  }
  if (typeof document !== 'undefined') {
    initializeInventoryRegistration(document);
  }
})();
