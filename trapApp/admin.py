from django.contrib import admin
from django.utils.html import format_html
from .models import Brand, Event, ClothingItem, ClothingSize, Outfit


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
        'preview_image', 'name', 'brand', 'category',
        'formality', 'gender', 'color', 'pattern',
        'price_display', 'scraped_at',
    )
    list_filter    = ('brand', 'category', 'formality', 'gender', 'pattern', 'is_set')
    search_fields  = ('name', 'description', 'color', 'material')
    ordering       = ('-scraped_at',)
    readonly_fields = ('scraped_at', 'preview_image_large')
    filter_horizontal = ('events',)
    inlines        = [ClothingSizeInline]

    fieldsets = (
        ('Основна інформація', {
            'fields': ('brand', 'name', 'description', 'category', 'formality', 'gender', 'is_set')
        }),
        ('Метадані (для матчингу)', {
            'fields': ('color', 'color_hex', 'material', 'pattern')
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
        ('Події', {
            'fields': ('events',)
        }),
    )

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
    exclude           = ()  # items керується через filter_horizontal

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

from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

admin.site.register(CustomUser, UserAdmin)