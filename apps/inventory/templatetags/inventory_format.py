from django import template

from inventory.formatting import money_co, number_co, quantity_co

register = template.Library()
register.filter('money_co', money_co)
register.filter('number_co', number_co)
register.filter('quantity_co', quantity_co)
