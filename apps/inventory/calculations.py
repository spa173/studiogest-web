from decimal import Decimal, ROUND_HALF_UP, localcontext

MAX_STOCK = Decimal('999999999999.999')
PRICE_STEP = Decimal('0.00000001')


def purchase_values(count, content, total_cost, sale_price, usage_price=None):
    with localcontext() as context:
        context.prec = 48
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            raise ValueError('La cantidad de presentaciones debe ser un entero positivo.')
        for value in [content, total_cost, sale_price] + ([] if usage_price is None else [usage_price]):
            if not value.is_finite() or value < 0:
                raise ValueError('Las cantidades y precios deben ser finitos y no negativos.')
        if content <= 0:
            raise ValueError('El contenido debe ser mayor que cero.')
        quantity = content * count
        if quantity > MAX_STOCK:
            raise ValueError('La cantidad recibida supera el límite de existencias.')
        proportional = sale_price / content
        return {
            'quantity': quantity,
            'cost_per_presentation': total_cost / count,
            'cost_per_base_unit': (total_cost / quantity).quantize(PRICE_STEP, rounding=ROUND_HALF_UP),
            'proportional_price': proportional.quantize(PRICE_STEP, rounding=ROUND_HALF_UP),
            'usage_price': (proportional if usage_price is None else usage_price).quantize(PRICE_STEP, rounding=ROUND_HALF_UP),
        }
