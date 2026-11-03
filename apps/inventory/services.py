import hashlib
import json
import uuid
from decimal import Decimal

from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from .calculations import MAX_STOCK, purchase_values
from .models import Product, StockEntry

TOKEN_SALT = 'inventory.purchase'


def operation_token(user, product, mode):
    return signing.dumps({'key': str(uuid.uuid4()), 'user': user.pk,
                          'product': product.pk if product else None, 'mode': mode}, salt=TOKEN_SALT)


def verify_token(token, user, product, mode):
    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=43200)
        if (payload['user'], payload['product'], payload['mode']) != (user.pk, product.pk if product else None, mode):
            raise ValueError
        return uuid.UUID(payload['key'])
    except (signing.BadSignature, KeyError, ValueError, TypeError):
        raise ValidationError('El formulario expiró o no es válido. Vuelve a abrirlo desde Inventario.')


def request_fingerprint(data):
    payload = {key: data.getlist(key) for key in sorted(data) if key not in ['csrfmiddlewaretoken', 'operation_token']}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


@transaction.atomic
def save_registration(*, data, user, key, fingerprint, product=None, mode='new'):
    if not user.is_active or not user.is_admin:
        raise ValidationError('Solo los administradores pueden registrar productos o compras.')
    previous = StockEntry.objects.filter(operation_key=key).first()
    if previous:
        if previous.created_by_id != user.pk or previous.request_fingerprint != fingerprint:
            raise ValidationError('La operación ya se registró con otros datos. Abre un formulario nuevo.')
        return previous.product, False
    if mode == 'new' and product is not None:
        raise ValidationError('El saldo inicial solo se registra al dar de alta un producto nuevo.')
    if product:
        product = Product.objects.select_for_update().get(pk=product.pk)
        if data['base_unit'] != product.base_unit:
            raise ValidationError('No se puede cambiar la unidad de control del producto.')
        if product.content_per_presentation is not None and (
                data['content'] != product.content_per_presentation or data['presentation'] != product.presentation):
            raise ValidationError('No se puede cambiar la presentación de un producto ya configurado.')
    else:
        product = Product(code=data['code'], stock=Decimal('0'), acquisition_cost=0,
                          sale_price=0, service_usage_price=0)
    product.name = data['name']
    product.description = data['description']
    product.presentation = data['presentation']
    product.base_unit = data['base_unit']
    product.content_per_presentation = data['content']
    product.presentation_sale_price = data['presentation_sale_price']
    product.usage_price_override = data['usage_price']
    product.minimum_stock = data['minimum_stock']
    product.is_active = data['is_active']
    prices = purchase_values(1, data['content'], Decimal('0'), data['presentation_sale_price'], data['usage_price'])
    product.sale_price = prices['proportional_price']
    product.service_usage_price = prices['usage_price']
    if mode != 'edit':
        values = purchase_values(data['presentation_count'], data['content'], data['total_cost'],
                                 data['presentation_sale_price'], data['usage_price'])
        product.acquisition_cost = values['cost_per_base_unit']
        if product.stock + values['quantity'] > MAX_STOCK:
            raise ValidationError('La compra supera el límite de existencias del producto.')
    product.full_clean()
    if not product.pk:
        product.save(force_insert=True)
    else:
        product.save(update_fields=['name', 'description', 'presentation', 'base_unit',
                                    'content_per_presentation', 'presentation_sale_price',
                                    'minimum_stock', 'is_active', 'sale_price',
                                    'service_usage_price', 'acquisition_cost', 'usage_price_override'])
    if mode == 'edit':
        return product, True
    StockEntry.objects.create(
        product=product, kind=StockEntry.Kind.INITIAL if mode == 'new' else StockEntry.Kind.PURCHASE,
        operation_key=key, request_fingerprint=fingerprint,
        presentation_count=data['presentation_count'], content_per_presentation=data['content'],
        base_unit=product.base_unit, quantity=values['quantity'], total_cost=data['total_cost'],
        presentation_sale_price=data['presentation_sale_price'], usage_price=values['usage_price'],
        presentation=product.presentation, created_by=user)
    updated = Product.objects.filter(pk=product.pk, stock__lte=MAX_STOCK-values['quantity']).update(
        stock=F('stock') + values['quantity'])
    if updated != 1:
        raise ValidationError('No se pudo actualizar el stock de forma segura.')
    return product, True
