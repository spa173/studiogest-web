"""Pure pricing rules. price_cop is always the final, already discounted total."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError

MAX_COP = Decimal('999999999999')


def decimal_value(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError({field: 'Ingresa un importe numérico válido.'})
    if not result.is_finite():
        raise ValidationError({field: 'Ingresa un importe numérico finito.'})
    return result


def validate_cop(value, field):
    amount = decimal_value(value, field)
    if amount < 0 or amount > MAX_COP or amount != amount.to_integral_value():
        raise ValidationError({field: 'Ingresa pesos enteros entre 0 y 999999999999.'})
    return amount


def calculate_pricing(adjusted_price, discount_type='NONE', discount_value=0):
    base = validate_cop(adjusted_price, 'adjusted_price_cop')
    value = decimal_value(discount_value, 'discount_value')
    if value < 0:
        raise ValidationError({'discount_value': 'El descuento no puede ser negativo.'})
    if discount_type == 'NONE':
        if value != 0:
            raise ValidationError({'discount_value': 'Selecciona un tipo de descuento.'})
        amount = Decimal('0')
    elif discount_type == 'PERCENT':
        if value > 100 or value != value.quantize(Decimal('0.01')):
            raise ValidationError({'discount_value': 'El porcentaje debe estar entre 0 y 100, con hasta dos decimales.'})
        amount = (base * value / Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    elif discount_type == 'FIXED':
        amount = validate_cop(value, 'discount_value')
        if amount > base:
            raise ValidationError({'discount_value': 'El descuento no puede superar el precio ajustado.'})
    else:
        raise ValidationError({'discount_type': 'Selecciona un tipo de descuento válido.'})
    return amount, base - amount
