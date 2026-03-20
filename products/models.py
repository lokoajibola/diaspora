from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    class CountryChoices(models.TextChoices):
        NIGERIA = 'NG', 'Nigeria'
        GHANA = 'GH', 'Ghana'

    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'vendor'})
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    country = models.CharField(max_length=2, choices=CountryChoices.choices, default=CountryChoices.NIGERIA)
    name = models.CharField(max_length=255)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=12, decimal_places=2)  # Price vendor receives
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # Default markup of 10%
    image = models.ImageField(upload_to='products/')
    stock = models.PositiveIntegerField(default=1)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_promoted = models.BooleanField(default=False)
    promotion_expires_at = models.DateTimeField(null=True, blank=True)

    def active_promotion(self):
        """Check if the promotion is still valid"""
        if self.is_promoted and self.promotion_expires_at:
            return self.promotion_expires_at > timezone.now()
        return False

    @property
    def selling_price(self):
        """Calculates price shown to customer: Base + Markup"""
        markup_amount = (self.base_price * self.markup_percentage) / 100
        return self.base_price + markup_amount

    @property
    def discounted_price(self):
        if self.discount_percentage and self.discount_percentage > 0:
            discount_amount = (self.selling_price * self.discount_percentage) / 100
            return self.selling_price - discount_amount
        return self.selling_price
    
    @property
    def total_price(self):
        if self.base_price is None:
            return Decimal('0.00')

        return self.discounted_price

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} image"