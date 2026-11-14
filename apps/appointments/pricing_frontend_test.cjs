const assert = require('node:assert/strict');
const {calculateAppointmentPricing, updateAppointmentPricing} = require('../../static/js/appointment-pricing.js');

const cases = [
  ['320000', 'NONE', '0', 0n, 320000n],
  ['320000', 'PERCENT', '10', 32000n, 288000n],
  ['320000', 'FIXED', '32000', 32000n, 288000n],
  ['320000', 'PERCENT', '100', 320000n, 0n],
  ['1', 'PERCENT', '50', 1n, 0n],
  ['101', 'PERCENT', '0.5', 1n, 100n],
  ['999999999999', 'PERCENT', '99.99', 999899999999n, 100000000n],
  ['0', 'NONE', '0', 0n, 0n],
];
for (const [base, kind, value, discount, total] of cases) {
  assert.deepEqual(calculateAppointmentPricing(base, kind, value), {discount, total});
}
for (const args of [
  ['-1', 'NONE', '0'], ['1.5', 'NONE', '0'], ['1000000000000', 'NONE', '0'],
  ['320000', 'PERCENT', '-1'], ['320000', 'PERCENT', '100.01'],
  ['320000', 'PERCENT', '0.001'], ['320000', 'FIXED', '320001'],
  ['320000', 'FIXED', '0.5'], ['320000', 'NONE', '10'],
]) assert.throws(() => calculateAppointmentPricing(...args));

const nodes = {
  serviceSelect: {value: '1'}, adjusted_price_cop: {value: ''},
  discount_type: {value: 'NONE'}, discount_value: {value: '0'},
  pricingError: {textContent: ''}, discountAmountDisplay: {value: ''},
  totalPriceDisplay: {value: ''}, appointmentForm: {dataset: {hasErrors: 'false'}},
};
const documentStub = {getElementById: id => nodes[id]};
const serviceCatalog = {'1': {price_cop: '250000'}};
const updatePricing = () => updateAppointmentPricing(false, documentStub, serviceCatalog);
updatePricing();
assert.equal(nodes.adjusted_price_cop.value, '250000');
nodes.adjusted_price_cop.value = '320000';
nodes.discount_type.value = 'PERCENT';
nodes.discount_value.value = '10';
updatePricing();
assert.match(nodes.totalPriceDisplay.value, /288[.,]000/);
nodes.appointmentForm.dataset.hasErrors = 'true';
updatePricing();
assert.equal(nodes.adjusted_price_cop.value, '320000');
assert.equal(nodes.discount_value.value, '10');
nodes.discount_value.value = '100';
updatePricing();
assert.equal(nodes.totalPriceDisplay.value, '$0 COP');
nodes.discount_value.value = '101';
updatePricing();
assert.ok(nodes.pricingError.textContent);
assert.equal(nodes.totalPriceDisplay.value, '');
nodes.discount_type.value = 'NONE';
nodes.discount_value.value = '0';
nodes.adjusted_price_cop.value = '0';
updatePricing();
assert.equal(nodes.totalPriceDisplay.value, '$0 COP');
delete nodes.adjusted_price_cop;
delete nodes.discount_type;
delete nodes.discount_value;
updatePricing();
assert.match(nodes.totalPriceDisplay.value, /250[.,]000/);
console.log('Pricing frontend: 8 calculation cases, 9 invalid cases and DOM behavior passed.');
