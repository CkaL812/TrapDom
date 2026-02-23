from django.contrib import admin
from .models import (
    DressCode, Event,
    Brand, Category, Color, Size, Tag,
    Product, ProductVariant, ProductImage,
    UserWardrobeItem, OutfitSuggestion
)

# --- Events ---
@admin.register(DressCode)
class DressCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'dress_code')
    list_filter = ('dress_code',)

# --- Brands & Products ---
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'website')
    search_fields = ('name', 'country')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code')

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'base_price', 'gender', 'season')
    list_filter = ('brand', 'category', 'gender', 'season', 'events')
    search_fields = ('name', 'brand__name')
    filter_horizontal = ('events', 'tags')
    inlines = [ProductVariantInline, ProductImageInline]

# --- Digital Wardrobe ---
@admin.register(UserWardrobeItem)
class UserWardrobeItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_identifier', 'color', 'category_guess', 'style', 'created_at')
    list_filter = ('style',)
    search_fields = ('user_identifier', 'color', 'category_guess')

@admin.register(OutfitSuggestion)
class OutfitSuggestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'wardrobe_item', 'event', 'created_at')
    list_filter = ('event',)
    filter_horizontal = ('suggested_products',)
