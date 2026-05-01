from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password as _check_password
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify


# ══════════════════════════════════════════════════════════════════
#   ГЛОБАЛЬНІ FORMALITY CHOICES (рівно 10, як у JS)
# ══════════════════════════════════════════════════════════════════
FORMALITY_CHOICES = [
    ('white_tie',          'White Tie'),
    ('black_tie',          'Black Tie'),
    ('black_tie_creative', 'Black Tie Creative'),
    ('business_formal',    'Business Formal'),
    ('business_casual',    'Business Casual'),
    ('smart_casual',       'Smart Casual'),
    ('cocktail',           'Cocktail'),
    ('after_five',         'After Five (A5)'),
    ('festival_chic',      'Festival Chic'),
    ('semi_formal',        'Semi-Formal'),
]


# ══════════════════════════════════════════════════════════════════
#                        BRAND
# ══════════════════════════════════════════════════════════════════

class Brand(models.Model):
    name            = models.CharField(max_length=100, unique=True)
    website         = models.URLField()
    formality_range = models.CharField(
        max_length=50,
        help_text="Наприклад: 'smart_casual', 'cocktail', 'black_tie'"
    )
    logo            = models.ImageField(upload_to='brands/logos/', blank=True, null=True)
    slug            = models.SlugField(max_length=120, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ══════════════════════════════════════════════════════════════════
#                        SEASON
# ══════════════════════════════════════════════════════════════════

class Season(models.Model):
    SEASON_CHOICES = [
        ('spring', 'Весна'),
        ('summer', 'Літо'),
        ('autumn', 'Осінь'),
        ('winter', 'Зима'),
    ]
    name = models.CharField(max_length=10, choices=SEASON_CHOICES, unique=True)

    class Meta:
        verbose_name        = 'Сезон'
        verbose_name_plural = 'Сезони'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()

    @classmethod
    def ensure_all_exist(cls):
        for code, _ in cls.SEASON_CHOICES:
            cls.objects.get_or_create(name=code)


# ══════════════════════════════════════════════════════════════════
#                        STYLE
# ══════════════════════════════════════════════════════════════════

class Style(models.Model):
    STYLE_CHOICES = [
        ('minimalism',    'Minimalism'),
        ('old_money',     'Old Money'),
        ('streetwear',    'Streetwear'),
        ('gorpcore',      'Gorpcore'),
        ('grunge',        'Grunge'),
        ('cyberpunk',     'Cyberpunk / Techwear'),
        ('vintage',       'Vintage / Retro'),
        ('dark_academia', 'Dark Academia'),
        ('avant_garde',   'Avant-Garde'),
        ('workwear',      'Workwear'),
    ]
    name = models.CharField(max_length=30, choices=STYLE_CHOICES, unique=True)

    class Meta:
        verbose_name        = 'Стиль'
        verbose_name_plural = 'Стилі'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()

    @classmethod
    def ensure_all_exist(cls):
        for code, _ in cls.STYLE_CHOICES:
            cls.objects.get_or_create(name=code)


# ══════════════════════════════════════════════════════════════════
#                        EVENT
# ══════════════════════════════════════════════════════════════════

class Event(models.Model):
    name        = models.CharField(max_length=150)
    formality   = models.CharField(max_length=30, choices=FORMALITY_CHOICES)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ══════════════════════════════════════════════════════════════════
#                        CLOTHING ITEM
# ══════════════════════════════════════════════════════════════════

class ClothingItem(models.Model):

    CATEGORY_CHOICES = [
        ('tops',      'Верх'),
        ('layering',  'Другий шар'),
        ('bottoms',   'Низ'),
        ('onepiece',  'Суцільний одяг'),
        ('outerwear', 'Верхній одяг'),
        ('footwear',  'Взуття'),
        ('accessory', 'Аксесуари'),
    ]

    SUBCATEGORY_CHOICES = [
        # tops
        ('t_shirt', 'Футболка'), ('shirt', 'Сорочка'), ('blouse', 'Блуза'),
        ('polo', 'Поло'), ('tank_top', 'Майка'), ('long_sleeve', 'Лонгслів'),
        ('crop_top', 'Кроп-топ'),
        # layering
        ('blazer', 'Блейзер / Піджак'), ('cardigan', 'Кардиган'),
        ('sweater', 'Светр'), ('hoodie', 'Худі'), ('sweatshirt', 'Світшот'),
        ('vest', 'Жилет'), ('suit_set', 'Костюм (комплект)'),
        # bottoms
        ('jeans', 'Джинси'), ('trousers', 'Штани'), ('linen_pants', 'Лляні штани'),
        ('shorts', 'Шорти'), ('skirt', 'Спідниця'), ('leggings', 'Легінси'),
        # onepiece
        ('dress', 'Сукня'), ('sundress', 'Сарафан'), ('jumpsuit', 'Комбінезон'),
        ('swimsuit', 'Купальник'), ('bikini', 'Бікіні'),
        # outerwear
        ('coat', 'Пальто'), ('wool_coat', 'Вовняне пальто'), ('trench', 'Тренч'),
        ('puffer', 'Пуховик'), ('quilted_jacket', 'Стьобана куртка'),
        ('leather_jacket', 'Шкіряна куртка'), ('denim_jacket', 'Джинсова куртка'),
        ('bomber', 'Бомбер'), ('parka', 'Парка'), ('fur_coat', 'Хутряна куртка'),
        # footwear
        ('sneakers', 'Кросівки'), ('boots', 'Черевики'),
        ('winter_boots', 'Зимові чоботи'), ('cowboy_boots', 'Ковбойські чоботи'),
        ('loafers', 'Лофери'), ('oxford_shoes', 'Оксфорди'),
        ('heels', 'Туфлі на підборах'), ('flats', 'Балетки'),
        ('sandals', 'Сандалі'), ('flip_flops', 'Шльопанці'),
        # accessory
        ('belt', 'Ремінь'), ('tie', 'Краватка'), ('scarf', 'Шарф / Хустка'),
        ('hat', 'Головний убір'), ('sunglasses', 'Окуляри'),
        ('jewelry', 'Прикраси'), ('earrings', 'Сережки'),
        ('bracelet', 'Браслет'), ('bag', 'Сумка'), ('tote', 'Шопер'),
        ('clutch', 'Клатч'), ('socks', 'Шкарпетки'),
        ('other_accessory', 'Інший аксесуар'),
    ]

    SUBCATEGORY_BY_CATEGORY = {
        'tops':      ['t_shirt', 'shirt', 'blouse', 'polo', 'tank_top', 'long_sleeve', 'crop_top'],
        'layering':  ['blazer', 'cardigan', 'sweater', 'hoodie', 'sweatshirt', 'vest', 'suit_set'],
        'bottoms':   ['jeans', 'trousers', 'linen_pants', 'shorts', 'skirt', 'leggings'],
        'onepiece':  ['dress', 'sundress', 'jumpsuit', 'swimsuit', 'bikini'],
        'outerwear': ['coat', 'wool_coat', 'trench', 'puffer', 'quilted_jacket',
                      'leather_jacket', 'denim_jacket', 'bomber', 'parka', 'fur_coat'],
        'footwear':  ['sneakers', 'boots', 'winter_boots', 'cowboy_boots', 'loafers',
                      'oxford_shoes', 'heels', 'flats', 'sandals', 'flip_flops'],
        'accessory': ['belt', 'tie', 'scarf', 'hat', 'sunglasses', 'jewelry',
                      'earrings', 'bracelet', 'bag', 'tote', 'clutch', 'socks', 'other_accessory'],
    }

    PATTERN_CHOICES = [
        ('solid',    'Однотонний'),
        ('striped',  'Смугастий'),
        ('checked',  'Клітинка'),
        ('print',    'Принт'),
        ('floral',   'Квітковий'),
        ('abstract', 'Абстрактний'),
    ]

    GENDER_CHOICES = [
        ('M', 'Чоловіче'),
        ('F', 'Жіноче'),
        ('U', 'Унісекс'),
    ]

    TAG_SOURCE_CHOICES = [
        ('scraper', 'Скрепер'),
        ('manual',  'Вручну'),
        ('ml_v1',   'ML v1 (CLIP)'),
        ('rules',   'Правила'),
        ('mixed',   'CLIP + правила'),
    ]

    VALID_TIMES_OF_DAY = ['morning', 'day', 'evening', 'night']
    VALID_AGE_RANGES   = ['13-17', '18-24', '25-34', '35-44', '45-54', '55+']

    # ─── Поля ───
    brand       = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='items')
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(
        max_length=30, choices=SUBCATEGORY_CHOICES,
        default='other_accessory',
        help_text='Конкретний тип одягу. Обов\'язково заповнити (тагер або вручну).',
    )

    formality   = models.CharField(max_length=30, choices=FORMALITY_CHOICES,
                                   default='smart_casual')
    source_url  = models.CharField(max_length=255, unique=True)
    scraped_at  = models.DateTimeField(auto_now_add=True)

    color       = models.CharField(max_length=100, blank=True)
    color_hex   = models.CharField(max_length=7, blank=True)
    material    = models.CharField(max_length=100, blank=True)
    pattern     = models.CharField(max_length=20, choices=PATTERN_CHOICES, default='solid')
    gender      = models.CharField(max_length=10, choices=GENDER_CHOICES, default='U')
    is_set      = models.BooleanField(default=False)

    price       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency    = models.CharField(max_length=3, default='UAH')
    sale_price  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    image_url   = models.URLField(blank=True, max_length=500)
    image_local = models.ImageField(upload_to='clothing/', blank=True, null=True)

    events  = models.ManyToManyField(Event,  blank=True,  related_name='items')
    seasons = models.ManyToManyField(Season, blank=False, related_name='items')
    styles  = models.ManyToManyField(Style,  blank=True,  related_name='items')

    # {"time_of_day": [...], "age_ranges": [...], "confidence": {...}, "notes": "..."}
    tags = models.JSONField(default=dict, blank=True)

    tagged_at  = models.DateTimeField(null=True, blank=True)
    tag_source = models.CharField(max_length=20, choices=TAG_SOURCE_CHOICES, default='scraper')

    class Meta:
        verbose_name        = 'Одяг'
        verbose_name_plural = 'Одяг'
        ordering            = ['-scraped_at']
        indexes = [
            models.Index(fields=['gender', 'category']),
            models.Index(fields=['category', 'subcategory']),
            models.Index(fields=['formality', 'gender']),
            models.Index(fields=['brand', 'gender']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return f"{self.brand.name} — {self.name}"

    # ─── seasons ───
    def seasons_display(self):
        return ', '.join(s.get_name_display() for s in self.seasons.all())
    seasons_display.short_description = 'Сезони'

    def set_seasons(self, codes):
        if not codes:
            raise ValidationError('Потрібен хоча б один сезон')
        valid = {c for c, _ in Season.SEASON_CHOICES}
        bad = [c for c in codes if c not in valid]
        if bad:
            raise ValidationError(f'Невідомі сезони: {bad}')
        self.seasons.set([Season.objects.get_or_create(name=c)[0] for c in codes])

    # ─── styles ───
    def styles_display(self):
        return ', '.join(s.get_name_display() for s in self.styles.all())
    styles_display.short_description = 'Стилі'

    def set_styles(self, codes):
        if not codes:
            self.styles.clear()
            return
        valid = {c for c, _ in Style.STYLE_CHOICES}
        bad = [c for c in codes if c not in valid]
        if bad:
            raise ValidationError(f'Невідомі стилі: {bad}')
        self.styles.set([Style.objects.get_or_create(name=c)[0] for c in codes])

    # ─── JSON-теги ───
    def _ensure_tags(self):
        if not isinstance(self.tags, dict):
            self.tags = {}

    def set_time_of_day(self, values):
        self._ensure_tags()
        bad = [v for v in values if v not in self.VALID_TIMES_OF_DAY]
        if bad:
            raise ValidationError(f'Невідомий час доби: {bad}')
        self.tags['time_of_day'] = list(values)

    def set_age_ranges(self, values):
        self._ensure_tags()
        bad = [v for v in values if v not in self.VALID_AGE_RANGES]
        if bad:
            raise ValidationError(f'Невідомий віковий діапазон: {bad}')
        self.tags['age_ranges'] = list(values)

    def set_confidence(self, scores_dict):
        """scores_dict = {'subcategory': 0.82, 'style': 0.64, 'formality': 0.71}"""
        self._ensure_tags()
        self.tags['confidence'] = scores_dict

    def get_time_of_day(self):
        return (self.tags or {}).get('time_of_day', [])

    def get_age_ranges(self):
        return (self.tags or {}).get('age_ranges', [])

    def mark_tagged(self, source='ml_v1'):
        self.tagged_at  = timezone.now()
        self.tag_source = source
        self.save(update_fields=['tagged_at', 'tag_source'])

    def clean(self):
        super().clean()
        allowed = self.SUBCATEGORY_BY_CATEGORY.get(self.category, [])
        if self.subcategory and allowed and self.subcategory not in allowed:
            raise ValidationError({
                'subcategory': f'Підкатегорія "{self.subcategory}" не підходить '
                               f'до категорії "{self.category}"'
            })
        if self.pk and not self.seasons.exists():
            raise ValidationError({'seasons': 'Треба вказати хоча б один сезон'})


@receiver(post_save, sender=ClothingItem)
def _warn_if_no_seasons(sender, instance, created, **kwargs):
    if not created and not instance.seasons.exists():
        import logging
        logging.getLogger(__name__).warning(
            f'ClothingItem #{instance.pk} ({instance.name}) не має сезонів'
        )


# ══════════════════════════════════════════════════════════════════
#                        REST
# ══════════════════════════════════════════════════════════════════

class ClothingSize(models.Model):
    item       = models.ForeignKey(ClothingItem, on_delete=models.CASCADE, related_name='sizes')
    size_label = models.CharField(max_length=10)
    size_type  = models.CharField(max_length=10,
        choices=[('alpha', 'Літерний (S/M/L)'), ('numeric', 'Числовий (36/38)')],
        default='alpha')
    in_stock   = models.BooleanField(default=True)
    quantity   = models.PositiveIntegerField(null=True, blank=True)

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


# ══════════════════════════════════════════════════════════════════
#                        NOTE (НОТАТКИ / ЗАХОДИ)
# ══════════════════════════════════════════════════════════════════

class Note(models.Model):
    EVENT_CHOICES = [
        ('день народження',           'День народження'),
        ('ювілей',                    'Ювілей'),
        ('заручини',                  'Заручини'),
        ('розпис',                    'Розпис'),
        ('весільний банкет (гість)',   'Весільний банкет (гість)'),
        ('коктейльна вечірка',         'Коктейльна вечірка'),
        ('формальний вечір',          'Формальний вечір'),
        ('корпоратив',                'Корпоратив'),
        ('конференція',               'Конференція'),
        ('нетворкінг',                'Нетворкінг'),
        ('презентація',               'Презентація'),
        ('публічний виступ',          'Публічний виступ'),
        ('фотосесія',                 'Фотосесія'),
        ('випуск з університету',     'Випуск з університету'),
        ('театр',                     'Театр'),
        ('опера / філармонія',        'Опера / філармонія'),
        ('гала-вечір',                'Гала-вечір'),
        ('благодійний бал',           'Благодійний бал'),
        ('свято в родині',            'Свято в родині'),
        ('бранч / зустріч з друзями', 'Бранч / зустріч з друзями'),
    ]

    GENDER_CHOICES = [
        ('male',   'Чоловічий'),
        ('female', 'Жіночий'),
        ('unisex', 'Унісекс'),
    ]

    MODE_CHOICES = [
        ('auto',   'Автоматично'),
        ('manual', 'Вручну'),
    ]

    user              = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notes')
    event_name        = models.CharField(max_length=100, choices=EVENT_CHOICES)
    event_date        = models.DateField()
    event_time        = models.TimeField(null=True, blank=True)
    gender            = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
    mode              = models.CharField(max_length=10, choices=MODE_CHOICES, default='auto')
    outfit_items      = models.ManyToManyField(ClothingItem, blank=True, related_name='notes')
    outfit_locked     = models.BooleanField(default=False)  # True = user built manually, skip auto-gen
    notification_sent = models.BooleanField(default=False)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['event_date', 'event_time']
        verbose_name        = 'Нотатка'
        verbose_name_plural = 'Нотатки'

    def __str__(self):
        return f"{self.get_event_name_display()} — {self.event_date}"


# ══════════════════════════════════════════════════════════════════
#                     SAVED OUTFIT (збережені образи)
# ══════════════════════════════════════════════════════════════════

class SavedOutfit(models.Model):
    SOURCE_CHOICES = [
        ('picker',   'Підбір образу'),
        ('wardrobe', 'Гардероб'),
        ('note',     'Захід'),
    ]

    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saved_outfits')
    name       = models.CharField(max_length=200, blank=True)
    source     = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='picker')
    items      = models.ManyToManyField(ClothingItem, blank=True, related_name='saved_outfits')
    note       = models.ForeignKey(Note, on_delete=models.SET_NULL, null=True, blank=True, related_name='saved_outfits')
    photo      = models.ImageField(upload_to='wardrobe_uploads/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Збережений образ'
        verbose_name_plural = 'Збережені образи'

    def __str__(self):
        return f"{self.user.email} — {self.get_source_display()} — {self.created_at:%d.%m.%Y}"

    def get_cover(self):
        """Перше фото образу або фото завантажене користувачем."""
        if self.photo:
            return self.photo.url
        first = self.items.exclude(image_url='').first()
        if first:
            return first.image_local.url if first.image_local else first.image_url
        return None


# ══════════════════════════════════════════════════════════════════
#                     WISHLIST (обрані товари)
# ══════════════════════════════════════════════════════════════════

class WishlistItem(models.Model):
    user     = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='wishlist')
    item     = models.ForeignKey(ClothingItem, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ('user', 'item')
        ordering            = ['-added_at']
        verbose_name        = 'Обраний товар'
        verbose_name_plural = 'Обрані товари'

    def __str__(self):
        return f'{self.user.email} → {self.item.name}'


# ══════════════════════════════════════════════════════════════════
#                     ORDER (замовлення)
# ══════════════════════════════════════════════════════════════════

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Очікує підтвердження'),
        ('confirmed', 'Підтверджено'),
        ('shipped',   'Відправлено'),
        ('delivered', 'Доставлено'),
        ('cancelled', 'Скасовано'),
    ]

    user       = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    full_name  = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20)
    city       = models.CharField(max_length=100)
    address    = models.CharField(max_length=255)
    comment    = models.TextField(blank=True)

    total      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency   = models.CharField(max_length=3, default='UAH')

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Замовлення'
        verbose_name_plural = 'Замовлення'

    def __str__(self):
        return f'Замовлення #{self.pk} — {self.user.email}'


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item     = models.ForeignKey(ClothingItem, on_delete=models.SET_NULL, null=True, blank=True)
    name     = models.CharField(max_length=255)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    size     = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f'{self.name} x{self.quantity}'

    @property
    def subtotal(self):
        return self.price * self.quantity