"""
trapApp/cart.py  —  логіка кошика через Django-сесії
"""

CART_SESSION_KEY = 'trapdom_cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, item, size='', quantity=1):
        key = f"{item.id}_{size}"
        if key in self.cart:
            self.cart[key]['quantity'] += quantity
        else:
            if item.image_local:
                image = item.image_local.url
            elif item.image_url:
                image = item.image_url
            else:
                image = ''

            self.cart[key] = {
                'item_id':   item.id,
                'name':      item.name,
                'brand':     item.brand.name,
                'price':     str(item.sale_price or item.price or 0),
                'old_price': str(item.price) if item.sale_price else None,
                'currency':  item.currency,
                'image':     image,
                'size':      size,
                'quantity':  quantity,
            }
        self.save()

    def update(self, key, quantity):
        if key in self.cart:
            if quantity <= 0:
                self.remove(key)
            else:
                self.cart[key]['quantity'] = quantity
                self.save()

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.cart = self.session[CART_SESSION_KEY]
        self.save()

    def save(self):
        self.session.modified = True

    def __len__(self):
        return sum(e['quantity'] for e in self.cart.values())

    def __iter__(self):
        for key, entry in self.cart.items():
            yield {
                'key':       key,
                'item_id':   entry['item_id'],
                'name':      entry['name'],
                'brand':     entry['brand'],
                'price':     entry['price'],
                'old_price': entry.get('old_price'),
                'currency':  entry['currency'],
                'image':     entry['image'],
                'size':      entry['size'],
                'quantity':  entry['quantity'],
                'subtotal':  round(float(entry['price']) * entry['quantity'], 2),
            }

    @property
    def total(self):
        return round(sum(float(e['price']) * e['quantity'] for e in self.cart.values()), 2)

    @property
    def currency(self):
        for e in self.cart.values():
            return e.get('currency', 'UAH')
        return 'UAH'

    def to_list(self):
        return list(self.__iter__())