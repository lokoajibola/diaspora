from django.db import models
from django.conf import settings
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ('placed', 'Order Placed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('arrived', 'Arrived in Destination Country'),
        ('delivered', 'Delivered'),
    )
    
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

    @property
    def status_percentage(self):
        mapping = {'placed': 20, 'processing': 40, 'shipped': 60, 'arrived': 80, 'delivered': 100}
        return mapping.get(self.status, 0)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
        