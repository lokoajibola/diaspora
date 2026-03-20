from django.contrib import admin
from .models import Product, Category

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'country', 'base_price', 'selling_price', 'stock', 'is_active']
    list_filter = ['category', 'country', 'is_active', 'vendor']
    search_fields = ['name', 'vendor__phone_number']
    readonly_fields = ['selling_price']

admin.site.register(Category)