from django.contrib import admin
from .models import VendorPayout

@admin.register(VendorPayout)
class VendorPayoutAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'amount_owed', 'is_paid', 'payout_date']
    list_filter = ['is_paid', 'created_at']
    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_paid=True, payout_date=timezone.now())
    mark_as_paid.short_description = "Mark selected payouts as completed"