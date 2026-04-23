from django.contrib import admin
from django.utils.html import format_html
from .models import Brand, Event, ClothingItem, ClothingSize, Outfit, Season, Style


# ─── Inline: розміри всередині картки речі ───────────────────────────────────

class ClothingSizeInline(admin.TabularInline):
    model = ClothingSize
    extra = 1
    fields = ('size_label', 'size_type', 'in_stock', 'quantity')


class OutfitItemsInline(admin.TabularInline):
    model = Outfit.items.through
    extra = 1
    verbose_name = 'Річ у луці'
    verbose_name_plural = 'Речі у луці'


# ─── Brand ───────────────────────────────────────────────────────────────────

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display  = ('name', 'formality_range', 'website', 'item_count')
    search_fields = ('name',)
    ordering      = ('name',)

    @admin.display(description='Кількість речей')
    def item_count(self, obj):
        return obj.items.count()


# ─── Season ──────────────────────────────────────────────────────────────────

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display  = ('get_name_display', 'item_count')
    ordering      = ('name',)

    @admin.display(description='Речей')
    def item_count(self, obj):
        return obj.items.count()


# ─── Style (НОВЕ) ────────────────────────────────────────────────────────────

@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    list_display  = ('get_name_display', 'item_count')
    ordering      = ('name',)

    @admin.display(description='Речей')
    def item_count(self, obj):
        return obj.items.count()


# ─── Event ───────────────────────────────────────────────────────────────────

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = ('name', 'formality', 'item_count', 'outfit_count')
    list_filter   = ('formality',)
    search_fields = ('name',)
    ordering      = ('formality', 'name')

    @admin.display(description='Речей')
    def item_count(self, obj):
        return obj.items.count()

    @admin.display(description='Луків')
    def outfit_count(self, obj):
        return obj.outfits.count()


# ─── ClothingItem ─────────────────────────────────────────────────────────────

@admin.register(ClothingItem)
class ClothingItemAdmin(admin.ModelAdmin):
    list_display   = (
        'preview_image', 'name', 'brand',
        'category', 'subcategory',           # ← додано subcategory
        'formality', 'gender', 'color', 'pattern',
        'price_display',
        'tag_source_badge', 'seasons_short',  # ← нові колонки
        'scraped_at',
    )
    list_filter    = (
        'brand', 'category', 'subcategory',   # ← фільтр по subcategory
        'formality', 'gender', 'pattern', 'is_set',
        'tag_source',                          # ← фільтр по джерелу тегів
        'seasons', 'styles',                   # ← фільтр по M2M
    )
    search_fields  = ('name', 'description', 'color', 'material')
    ordering       = ('-scraped_at',)
    readonly_fields = (
        'scraped_at', 'preview_image_large',
        'tagged_at', 'tag_source', 'tags_pretty',  # ← теги readonly (їх ставить тагер)
        'confidence_pretty',                        # ← красивий вивід confidence
    )
    filter_horizontal = ('events', 'seasons', 'styles')  # ← додано seasons і styles
    inlines        = [ClothingSizeInline]

    fieldsets = (
        ('Основна інформація', {
            'fields': (
                'brand', 'name', 'description',
                'category', 'subcategory',           # ← subcategory поруч із category
                'formality', 'gender', 'is_set',
            )
        }),
        ('Метадані (для матчингу)', {
            'fields': ('color', 'color_hex', 'material', 'pattern')
        }),
        ('Сезони / Стилі / Події', {               # ← нова секція для M2M
            'fields': ('seasons', 'styles', 'events'),
            'description': 'M2M-поля. Сезони — обов\'язково (хоча б один).',
        }),
        ('🤖 ML-теги (заповнюється тагером)', {     # ← нова секція
            'fields': ('tag_source', 'tagged_at', 'confidence_pretty', 'tags_pretty'),
            'classes': ('collapse',),
            'description': 'Ці поля заповнює CLIP-тагер. Тільки для читання.',
        }),
        ('Ціна', {
            'fields': ('price', 'currency', 'sale_price')
        }),
        ('Медіа', {
            'fields': ('image_url', 'image_local', 'preview_image_large')
        }),
        ('Посилання та дати', {
            'fields': ('source_url', 'scraped_at')
        }),
    )

    # ─── Візуалізація ──────────────────────────────────────────────────

    @admin.display(description='Фото')
    def preview_image(self, obj):
        url = obj.image_url or (obj.image_local.url if obj.image_local else '')
        if url:
            return format_html('<img src="{}" style="height:48px;border-radius:4px;">', url)
        return '—'

    @admin.display(description='Фото (повне)')
    def preview_image_large(self, obj):
        url = obj.image_url or (obj.image_local.url if obj.image_local else '')
        if url:
            return format_html('<img src="{}" style="max-height:300px;border-radius:8px;">', url)
        return '—'

    @admin.display(description='Ціна')
    def price_display(self, obj):
        if obj.sale_price:
            return format_html(
                '<s style="color:gray">{}</s> <b style="color:green">{} {}</b>',
                obj.price, obj.sale_price, obj.currency
            )
        return f'{obj.price} {obj.currency}' if obj.price else '—'

    @admin.display(description='Сезони')
    def seasons_short(self, obj):
        """Коротке відображення M2M seasons у списку."""
        codes = list(obj.seasons.values_list('name', flat=True))
        if not codes:
            return format_html('<span style="color:#999">—</span>')
        emoji = {'spring': '🌸', 'summer': '☀️', 'autumn': '🍂', 'winter': '❄️'}
        return ' '.join(emoji.get(c, c) for c in codes)

    @admin.display(description='Джерело тегів')
    def tag_source_badge(self, obj):
        """Кольоровий бейдж для tag_source."""
        if not obj.tagged_at:
            return format_html('<span style="color:#c33">⚠ не затеговано</span>')
        colors = {
            'scraper': '#888',
            'manual':  '#2a7',
            'ml_v1':   '#27a',
            'rules':   '#a72',
            'mixed':   '#7a2',
        }
        color = colors.get(obj.tag_source, '#888')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:3px;font-size:11px">{}</span>',
            color, obj.get_tag_source_display()
        )

    @admin.display(description='Теги (JSON)')
    def tags_pretty(self, obj):
        """Форматований JSON для читабельності в адмінці."""
        if not obj.tags:
            return format_html('<em style="color:#999">порожньо</em>')

        tags = obj.tags or {}
        parts = []

        if 'time_of_day' in tags:
            parts.append(f"<b>Час доби:</b> {', '.join(tags['time_of_day'])}")
        if 'age_ranges' in tags:
            parts.append(f"<b>Вік:</b> {', '.join(tags['age_ranges'])}")
        if 'notes' in tags:
            parts.append(f"<b>Замітки:</b> {tags['notes']}")

        if not parts:
            return format_html('<em>{}</em>', str(tags))
        return format_html('<br>'.join(parts))

    @admin.display(description='Впевненість CLIP')
    def confidence_pretty(self, obj):
        """Показує confidence-скори CLIP у зрозумілому вигляді."""
        conf = (obj.tags or {}).get('confidence', {})
        if not conf:
            return format_html('<em style="color:#999">немає даних</em>')

        def bar(value):
            pct = int(value * 100)
            # Зелений якщо > 25%, жовтий 15-25%, червоний < 15%
            color = '#27a745' if value >= 0.25 else ('#ffc107' if value >= 0.15 else '#dc3545')
            return (
                f'<div style="display:inline-block;width:80px;height:10px;'
                f'background:#333;border-radius:2px;vertical-align:middle;margin:0 6px">'
                f'<div style="width:{min(pct*3,100)}%;height:100%;background:{color};'
                f'border-radius:2px"></div></div>{value:.2f}'
            )

        lines = []
        if 'subcategory' in conf:
            lines.append(f"<b>Підкатегорія:</b> {bar(conf['subcategory'])}")
        if 'formality' in conf:
            lines.append(f"<b>Дрес-код:</b> {bar(conf['formality'])}")
        if 'styles' in conf and isinstance(conf['styles'], dict):
            for style, score in conf['styles'].items():
                lines.append(f"<b>{style}:</b> {bar(score)}")

        return format_html('<br>'.join(lines))


# ─── ClothingSize ─────────────────────────────────────────────────────────────

@admin.register(ClothingSize)
class ClothingSizeAdmin(admin.ModelAdmin):
    list_display  = ('item', 'size_label', 'size_type', 'in_stock', 'quantity')
    list_filter   = ('size_type', 'in_stock')
    search_fields = ('item__name', 'size_label')
    ordering      = ('item', 'size_label')


# ─── Outfit ───────────────────────────────────────────────────────────────────

@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display      = ('name', 'event', 'item_count', 'created')
    list_filter       = ('event__formality', 'event')
    search_fields     = ('name', 'notes')
    ordering          = ('-created',)
    readonly_fields   = ('created',)
    filter_horizontal = ('items',)
    exclude           = ()

    fieldsets = (
        (None, {
            'fields': ('name', 'event', 'notes', 'created')
        }),
        ('Речі в луці', {
            'fields': ('items',)
        }),
    )

    @admin.display(description='Речей у луці')
    def item_count(self, obj):
        return obj.items.count()


# ─── Custom User ──────────────────────────────────────────────────────────────

from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

admin.site.register(CustomUser, UserAdmin)