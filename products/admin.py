from django.contrib import admin
from .models import Product, Category, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'base_price', 'selling_price', 'stock', 'is_active']
    list_filter = ['category', 'is_active', 'vendor']
    search_fields = ['name', 'vendor__phone_number']
    readonly_fields = ['selling_price']
    inlines = [ProductImageInline]

admin.site.register(Category)