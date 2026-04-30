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


def wishlist_context(request):
    if request.user.is_authenticated:
        from .models import WishlistItem
        ids = set(WishlistItem.objects.filter(user=request.user).values_list('item_id', flat=True))
    else:
        ids = set()
    return {'wishlist_ids': ids}