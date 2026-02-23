from django.db import models


# -------------------------
# EVENTS
# -------------------------

class DressCode(models.Model):
    name = models.CharField(max_length=100)  # Formal, Casual, Smart Casual
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=255)
    dress_code = models.ForeignKey(DressCode, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# -------------------------
# BRANDS
# -------------------------

class Brand(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = models.URLField(blank=True)

    def __str__(self):
        return self.name


# -------------------------
# CATEGORIES
# -------------------------

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories"
    )

    def __str__(self):
        return self.name


# -------------------------
# COLORS
# -------------------------

class Color(models.Model):
    name = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return self.name


# -------------------------
# SIZES
# -------------------------

class Size(models.Model):
    name = models.CharField(max_length=20)  # S, M, L, XL

    def __str__(self):
        return self.name


# -------------------------
# PRODUCTS
# -------------------------

class Product(models.Model):

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('unisex', 'Unisex'),
    )

    SEASON_CHOICES = (
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('spring', 'Spring'),
        ('autumn', 'Autumn'),
        ('all', 'All Season'),
    )

    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    season = models.CharField(max_length=20, choices=SEASON_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    events = models.ManyToManyField(Event, related_name="recommended_products")
    tags = models.ManyToManyField("Tag", blank=True)

    def __str__(self):
        return self.name


# -------------------------
# PRODUCT VARIANTS
# -------------------------

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.size.name} - {self.color.name}"


# -------------------------
# PRODUCT IMAGES
# -------------------------

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField()
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return self.product.name


# -------------------------
# TAGS
# -------------------------

class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# -------------------------
# DIGITAL WARDROBE (NEW)
# -------------------------

class UserWardrobeItem(models.Model):
    user_identifier = models.CharField(max_length=255, help_text="Session ID or User ID")
    image = models.ImageField(upload_to="wardrobe_uploads/")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional fields that AI might fill in
    color = models.CharField(max_length=50, blank=True)
    category_guess = models.CharField(max_length=100, blank=True)
    style = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Wardrobe Item {self.id} from {self.user_identifier}"


class OutfitSuggestion(models.Model):
    wardrobe_item = models.ForeignKey(UserWardrobeItem, on_delete=models.CASCADE, related_name="suggestions")
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    suggested_products = models.ManyToManyField(Product, related_name="suggested_in_outfits")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # The raw reasoning from the AI
    ai_reasoning = models.TextField(blank=True)
    
    def __str__(self):
        return f"Suggestion for {self.wardrobe_item} at {self.event.name}"
