from django.db import models
from django.conf import settings
from products.models import Product


class PayoutRequest(models.Model):
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor.shop_name} - {self.amount}"
        
class Order(models.Model):
    # Tracking Stages for Admin and Customer
    STATUS_CHOICES = [
        ('pending', 'Pending (Unpaid)'),
        ('paid', 'Paid/Processing'),
        ('shipped', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed')
    created_at = models.DateTimeField(auto_now_add=True)
    paystack_ref = models.CharField(max_length=100, blank=True)
    # ... existing fields (customer, total_amount, etc.) ...
    receiver_name = models.CharField(max_length=255, default='John Doe')
    receiver_phone = models.CharField(max_length=20, default='0000000000')
    delivery_address = models.TextField(max_length=20, default='UK')
    country = models.CharField(max_length=100, default='UK')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def status_percentage(self):
        # Match these keys to the FIRST values in STATUS_CHOICES above
        mapping = {
            'pending': 20, 
            'paid': 50, 
            'shipped': 80, 
            'delivered': 100,
            'cancelled': 0
        }
        return mapping.get(self.status, 0)

    class Meta:
        ordering = ['-created_at'] # Shows newest orders first for Admin/Customer

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    # ADD THIS:
    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
        