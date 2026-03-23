from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class Brand(models.Model):
    name            = models.CharField(max_length=100, unique=True)
    website         = models.URLField()
    formality_range = models.CharField(
        max_length=50,
        help_text="Наприклад: 'casual', 'smart_casual', 'formal', 'black_tie'"
    )
    # ✅ НОВЕ: логотип бренду
    logo            = models.ImageField(upload_to='brands/logos/', blank=True, null=True)
    # ✅ НОВЕ: slug для URL /brands/zara/
    slug            = models.SlugField(max_length=120, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Season(models.Model):
    SEASON_CHOICES = [
        ('spring', 'Весна'),
        ('summer', 'Літо'),
        ('autumn', 'Осінь'),
        ('winter', 'Зима'),
    ]
    name = models.CharField(max_length=10, choices=SEASON_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


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
    name        = models.CharField(max_length=150)
    formality   = models.CharField(max_length=20, choices=FORMALITY_CHOICES)
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

    brand       = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='items')
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    formality   = models.CharField(max_length=20, choices=FORMALITY_CHOICES)
    source_url  = models.CharField(max_length=255, unique=True)
    scraped_at  = models.DateTimeField(auto_now_add=True)

    color       = models.CharField(max_length=100, blank=True)
    color_hex   = models.CharField(max_length=7, blank=True)
    material    = models.CharField(max_length=100, blank=True)
    pattern     = models.CharField(max_length=20, choices=PATTERN_CHOICES, default='solid')
    gender      = models.CharField(
        max_length=10,
        choices=[('M', 'Чоловіче'), ('F', 'Жіноче'), ('U', 'Унісекс')],
        default='U'
    )
    is_set      = models.BooleanField(default=False)

    price       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency    = models.CharField(max_length=3, default='UAH')
    sale_price  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    image_url   = models.URLField(blank=True)
    image_local = models.ImageField(upload_to='clothing/', blank=True, null=True)

    events      = models.ManyToManyField(Event, blank=True, related_name='items')
    seasons     = models.ManyToManyField(Season, blank=True, related_name='items')

    def __str__(self):
        return f"{self.brand.name} — {self.name}"


class ClothingSize(models.Model):
    item       = models.ForeignKey(ClothingItem, on_delete=models.CASCADE, related_name='sizes')
    size_label = models.CharField(max_length=10)
    size_type  = models.CharField(
        max_length=10,
        choices=[('alpha', 'Літерний (S/M/L)'), ('numeric', 'Числовий (36/38)')],
        default='alpha'
    )
    in_stock  = models.BooleanField(default=True)
    quantity  = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.item.name} — {self.size_label}"


class Outfit(models.Model):
    name    = models.CharField(max_length=200)
    event   = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, related_name='outfits')
    items   = models.ManyToManyField(ClothingItem, related_name='outfits')
    created = models.DateTimeField(auto_now_add=True)
    notes   = models.TextField(blank=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=50)
    last_name  = models.CharField(max_length=50)
    email      = models.EmailField(unique=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email


from django.contrib.auth.hashers import make_password, check_password as _check_password


class AdminManager(models.Manager):
    def create_admin(self, email, password):
        if not email:
            raise ValueError("Email є обов'язковим")
        admin = self.model(email=email.lower().strip())
        admin.set_password(password)
        admin.save(using=self._db)
        return admin


class Admin(models.Model):
    email      = models.EmailField(unique=True)
    password   = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AdminManager()

    class Meta:
        verbose_name        = 'Адміністратор'
        verbose_name_plural = 'Адміністратори'

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return _check_password(raw_password, self.password)

    def __str__(self):
        return self.email