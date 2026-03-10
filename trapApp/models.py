from django.db import models


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)  # 'Zara', 'Hugo Boss', ...
    website = models.URLField()
    formality_range = models.CharField(
        max_length=50,
        help_text="Наприклад: 'casual', 'smart_casual', 'formal', 'black_tie'"
    )

    def __str__(self):
        return self.name


class Event(models.Model):
    FORMALITY_CHOICES = [
        ('casual',       'Casual'),
        ('smart_casual', 'Smart Casual'),
        ('business',     'Business'),
        ('cocktail',     'Cocktail'),
        ('formal',       'Formal'),
        ('black_tie',    'Black Tie'),
        ('white_tie',    'White Tie'),
    ]
    name = models.CharField(max_length=150)  # 'Гала-вечір', 'День народження', ...
    formality = models.CharField(max_length=20, choices=FORMALITY_CHOICES)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ClothingItem(models.Model):
    CATEGORY_CHOICES = [
        ('tops',      'Верх (Tops/Shirts)'),
        ('layering',  'Другий шар (Layering/Tailoring)'),
        ('bottoms',   'Низ (Bottoms)'),
        ('onepiece',  'Суцільний одяг (One-piece/Sets)'),
        ('outerwear', 'Верхній одяг (Outerwear)'),
        ('footwear',  'Взуття (Footwear)'),
        ('accessory', 'Аксесуари (Accessories)'),
    ]
    PATTERN_CHOICES = [
        ('solid',    'Однотонний'),
        ('striped',  'Смугастий'),
        ('checked',  'Клітинка'),
        ('print',    'Принт'),
        ('floral',   'Квітковий'),
        ('abstract', 'Абстрактний'),
    ]
    FORMALITY_CHOICES = [
        ('casual',       'Casual'),
        ('smart_casual', 'Smart Casual'),
        ('business',     'Business'),
        ('cocktail',     'Cocktail'),
        ('formal',       'Formal'),
        ('black_tie',    'Black Tie'),
    ]

    # --- Основна інформація ---
    brand        = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='items')
    name         = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    formality    = models.CharField(max_length=20, choices=FORMALITY_CHOICES)
    source_url   = models.URLField(unique=True)  # Оригінальна сторінка товару
    scraped_at   = models.DateTimeField(auto_now_add=True)

    # --- Метадані для матчингу ---
    color        = models.CharField(max_length=100, blank=True)  # 'Black', 'Navy Blue'
    color_hex    = models.CharField(max_length=7, blank=True)    # '#1a1a1a'
    material     = models.CharField(max_length=100, blank=True)  # 'Wool', 'Cotton Denim'
    pattern      = models.CharField(max_length=20, choices=PATTERN_CHOICES, default='solid')
    gender       = models.CharField(
        max_length=10,
        choices=[('M', 'Чоловіче'), ('F', 'Жіноче'), ('U', 'Унісекс')],
        default='U'
    )
    is_set       = models.BooleanField(default=False)  # True для костюмів/комплектів

    # --- Ціна ---
    price        = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency     = models.CharField(max_length=3, default='UAH')
    sale_price   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # --- Медіа ---
    image_url    = models.URLField(blank=True)
    image_local  = models.ImageField(upload_to='clothing/', blank=True, null=True)

    # --- Події, яким відповідає річ ---
    events       = models.ManyToManyField(Event, blank=True, related_name='items')

    def __str__(self):
        return f"{self.brand.name} — {self.name}"


class ClothingSize(models.Model):
    """Доступні розміри для конкретної речі."""
    item        = models.ForeignKey(ClothingItem, on_delete=models.CASCADE, related_name='sizes')
    size_label  = models.CharField(max_length=10)  # 'XS', 'S', 'M', 'L', 'XL', 'XXL', '38', '40'
    size_type   = models.CharField(
        max_length=10,
        choices=[('alpha', 'Літерний (S/M/L)'), ('numeric', 'Числовий (36/38)')],
        default='alpha'
    )
    in_stock    = models.BooleanField(default=True)
    quantity    = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.item.name} — {self.size_label}"


class Outfit(models.Model):
    """Готовий лук (капсула) зібраний для конкретної події."""
    name    = models.CharField(max_length=200)
    event   = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, related_name='outfits')
    items   = models.ManyToManyField(ClothingItem, related_name='outfits')
    created = models.DateTimeField(auto_now_add=True)
    notes   = models.TextField(blank=True)

    def __str__(self):
        return self.name

from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=50)
    last_name  = models.CharField(max_length=50)
    email      = models.EmailField(unique=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email