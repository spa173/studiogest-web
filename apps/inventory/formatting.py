from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

UNIT_SYMBOLS = {'UNIT': 'ud.', 'ML': 'ml', 'G': 'g'}


def number_co(value, places=8):
    if value is None or value == '':
        return '—'
    try:
        amount = Decimal(str(value))
        if not amount.is_finite():
            return '—'
        with localcontext() as context:
            context.prec = 48
            amount = amount.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
            if not amount:
                amount = abs(amount)
            integer, fraction = format(amount, f',.{places}f').split('.')
        integer = integer.replace(',', '.')
        fraction = fraction.rstrip('0')
        return integer + (',' + fraction if fraction else '')
    except (InvalidOperation, ValueError):
        return '—'


def money_co(value):
    number = number_co(value)
    return '$' + number if number != '—' else number


def quantity_co(value, unit):
    number = number_co(value, places=3)
    return f'{number} {UNIT_SYMBOLS.get(unit, unit)}' if number != '—' else number
