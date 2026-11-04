const assert = require('node:assert/strict');
const test = require('node:test');
const {initializeInventoryRegistration} = require('../../static/js/inventory-registration.js');

function setup({unit = 'ML', content = '50', count = '10', total = '100', sale = '20', usage = '', mode = 'new'} = {}) {
  const fields = Object.fromEntries(Object.entries({base_unit: unit, content, presentation_count: count,
    total_cost: total, presentation_sale_price: sale, usage_price: usage}).map(([key, value]) =>
    [key, {value, disabled: false, dataset: {locked: 'false'}}]));
  if (mode === 'edit') { delete fields.presentation_count; delete fields.total_cost; }
  const ids = Object.fromEntries(['preview-package-cost', 'preview-unit-cost', 'preview-proportional',
    'preview-usage', 'preview-quantity', 'preview-hint'].map(id => [id, {textContent: ''}]));
  const wrappers = {content: {hidden: false}, usage_price: {hidden: false}};
  const divisible = [{hidden: false}], units = [{textContent: ''}], handlers = {};
  const button = {disabled: false, textContent: ''};
  const form = {
    dataset: {mode}, elements: {namedItem: name => fields[name]},
    querySelector(selector) {
      if (selector === 'button[type="submit"]') return button;
      const match = /data-field="([^"]+)"/.exec(selector);
      return match ? wrappers[match[1]] : null;
    },
    querySelectorAll: selector => selector === '[data-divisible]' ? divisible : units,
    addEventListener: (event, handler) => { handlers[event] = handler; },
  };
  const document = {getElementById: id => id === 'inventory-registration' ? form : ids[id]};
  initializeInventoryRegistration(document);
  return {fields, ids, wrappers, handlers, button};
}

test('ejemplo: 10 frascos de 50 ml por 100, venta a 20', () => {
  const {ids} = setup();
  assert.equal(ids['preview-package-cost'].textContent, '$10');
  assert.equal(ids['preview-unit-cost'].textContent, '$0,2');
  assert.equal(ids['preview-proportional'].textContent, '$0,4');
  assert.equal(ids['preview-usage'].textContent, '$0,4');
  assert.equal(ids['preview-quantity'].textContent, '500 ml');
});
test('precio personalizado y recálculo al cambiar costo/contenido', () => {
  const state = setup({usage: '0.75'});
  assert.equal(state.ids['preview-usage'].textContent, '$0,75');
  state.fields.content.value = '100';
  state.handlers.input();
  assert.equal(state.ids['preview-unit-cost'].textContent, '$0,1');
  assert.equal(state.ids['preview-proportional'].textContent, '$0,2');
  assert.equal(state.ids['preview-usage'].textContent, '$0,75');
});
test('unidades ocultan volumen y tarifa; cambiar a gramos los habilita', () => {
  const state = setup({unit: 'UNIT'});
  assert.equal(state.wrappers.content.hidden, true);
  assert.equal(state.fields.content.disabled, true);
  assert.equal(state.ids['preview-quantity'].textContent, '10 unidades');
  state.fields.base_unit.value = 'G';
  state.handlers.change();
  assert.equal(state.wrappers.content.hidden, false);
  assert.equal(state.fields.content.disabled, false);
  assert.equal(state.ids['preview-quantity'].textContent, '500 g');
});
test('cero, cantidades incompletas y precisión de 8 decimales', () => {
  const state = setup({total: '0', sale: '0'});
  assert.equal(state.ids['preview-package-cost'].textContent, '$0');
  assert.equal(state.ids['preview-usage'].textContent, '$0');
  state.fields.presentation_count.value = '';
  state.handlers.input();
  assert.equal(state.ids['preview-package-cost'].textContent, '—');
  const small = setup({content: '3', total: '1', count: '1', sale: '1'});
  assert.equal(small.ids['preview-unit-cost'].textContent, '$0,33333333');
});
test('editar precios no necesita una compra; submit bloquea doble clic', () => {
  const state = setup({mode: 'edit'});
  assert.equal(state.ids['preview-proportional'].textContent, '$0,4');
  state.handlers.submit();
  assert.equal(state.button.disabled, true);
});

test('saldo inicial: 3 tubos de 250 ml, costo 150000, precio 85000', () => {
  const {ids} = setup({content: '250', count: '3', total: '150000', sale: '85000'});
  assert.equal(ids['preview-package-cost'].textContent, '$50.000');
  assert.equal(ids['preview-unit-cost'].textContent, '$200');
  assert.equal(ids['preview-proportional'].textContent, '$340');
  assert.equal(ids['preview-quantity'].textContent, '750 ml');
});
