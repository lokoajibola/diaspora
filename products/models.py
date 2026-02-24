from django.db import models
from django.conf import settings
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'vendor'})
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=12, decimal_places=2)  # Price vendor receives
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # Default markup of 10%
    image = models.ImageField(upload_to='products/')
    stock = models.PositiveIntegerField(default=1)
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
    def total_price(self):
        # The Guard Clause: 
        # If the product is being created and has no price yet, return 0
        if self.base_price is None:
            return Decimal('0.00')
            
        # Example: adding a 10% platform fee to the base_price
        # Using Decimal(1.1) instead of float 1.1 prevents errors
        return self.base_price * Decimal('1.1')

    def __str__(self):
        return self.name