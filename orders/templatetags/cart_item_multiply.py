from django import template
register = template.Library()

@register.filter
def cart_item_multiply(value):
    return value.quantity * value.menu.price