"""
trapApp/context_processors.py
Передає кількість товарів у кошику + список позицій у всі шаблони.
"""
from .cart import Cart


def cart_context(request):
    cart = Cart(request)
    return {
        'cart_count': len(cart),
        'cart_items': cart.to_list(),
        'cart_total': cart.total,
        'cart_currency': cart.currency,
    }