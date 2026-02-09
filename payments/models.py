from django.db import models
from django.conf import settings

class VendorPayout(models.Model):
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'vendor'})
    amount_owed = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payout_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor.phone_number} - ₦{self.amount_owed} ({'Paid' if self.is_paid else 'Pending'})"