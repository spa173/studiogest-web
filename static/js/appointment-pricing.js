// Preview only: the server independently validates and calculates all amounts.
function calculateAppointmentPricing(baseText, kind, valueText) {
  const max = 999999999999n;
  const cop = (text) => {
    if (!/^\d+$/.test(text)) throw new Error('Ingresa pesos enteros no negativos.');
    const value = BigInt(text);
    if (value > max) throw new Error('El importe supera el máximo permitido.');
    return value;
  };
  const base = cop(String(baseText));
  const text = String(valueText === '' ? '0' : valueText);
  let amount;
  if (kind === 'NONE') {
    if (!/^0+(?:\.0{1,2})?$/.test(text)) throw new Error('Selecciona un tipo de descuento.');
    amount = 0n;
  } else if (kind === 'PERCENT') {
    if (!/^(?:\d+|\d*\.\d{1,2})$/.test(text)) throw new Error('Ingresa un porcentaje válido con hasta dos decimales.');
    const parts = text.split('.');
    const hundredths = BigInt(parts[0] || '0') * 100n + BigInt((parts[1] || '').padEnd(2, '0'));
    if (hundredths > 10000n) throw new Error('El porcentaje no puede superar el 100 %.');
    // Exact half-up rounding to whole COP, even at the maximum supported price.
    amount = (base * hundredths + 5000n) / 10000n;
  } else if (kind === 'FIXED') {
    // DecimalField can render a saved integer with two zero decimals.
    amount = cop(text.replace(/\.0{1,2}$/, ''));
    if (amount > base) throw new Error('El descuento no puede superar el precio ajustado.');
  } else {
    throw new Error('Selecciona un tipo de descuento válido.');
  }
  return {discount: amount, total: base - amount};
}

function updateAppointmentPricing(resetPrice = false, documentRoot = document, serviceCatalog = servicesData) {
  const selected = documentRoot.getElementById('serviceSelect').value;
  const service = serviceCatalog[selected];
  const error = documentRoot.getElementById('pricingError');
  const discountDisplay = documentRoot.getElementById('discountAmountDisplay');
  const totalDisplay = documentRoot.getElementById('totalPriceDisplay');
  error.textContent = '';
  discountDisplay.value = '';
  totalDisplay.value = '';
  if (!service) return;
  const adjusted = documentRoot.getElementById('adjusted_price_cop');
  const kind = documentRoot.getElementById('discount_type');
  const value = documentRoot.getElementById('discount_value');
  const hasErrors = documentRoot.getElementById('appointmentForm').dataset.hasErrors === 'true';
  if (adjusted && (resetPrice || (adjusted.value === '' && !hasErrors))) adjusted.value = service.price_cop;
  if (value) value.step = kind.value === 'FIXED' ? '1' : '0.01';
  try {
    const result = calculateAppointmentPricing(
      adjusted && adjusted.value !== '' ? adjusted.value : service.price_cop,
      kind ? kind.value : 'NONE', value ? value.value : '0',
    );
    const format = (amount) => '$' + new Intl.NumberFormat('es-CO').format(Number(amount)) + ' COP';
    discountDisplay.value = format(result.discount);
    totalDisplay.value = format(result.total);
  } catch (problem) {
    error.textContent = problem.message;
  }
}

if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    for (const id of ['adjusted_price_cop', 'discount_type', 'discount_value']) {
      const field = document.getElementById(id);
      if (field) field.addEventListener('input', () => updateAppointmentPricing());
    }
    updateAppointmentPricing();
  });
}
if (typeof module !== 'undefined' && module.exports) module.exports = {calculateAppointmentPricing, updateAppointmentPricing};
