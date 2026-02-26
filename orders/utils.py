from decimal import Decimal
from collections import defaultdict

from .models import PayoutRequest
from users.models import Notification


def ensure_tracking_number(order):
    if not order.tracking_number:
        order.tracking_number = f"DW-{str(order.id).zfill(8)}"


def credit_vendors_for_paid_order(order):
    if order.vendor_credit_processed:
        return

    vendor_amounts = defaultdict(lambda: Decimal('0.00'))
    for item in order.items.select_related('product__vendor').all():
        line_total = item.price * item.quantity
        vendor_amounts[item.product.vendor] += line_total

    for vendor, amount in vendor_amounts.items():
        vendor.balance += amount
        vendor.save(update_fields=['balance'])

        pending_payout = PayoutRequest.objects.filter(vendor=vendor, is_paid=False).order_by('-created_at').first()
        if pending_payout:
            pending_payout.amount += amount
            pending_payout.save(update_fields=['amount'])
        else:
            PayoutRequest.objects.create(vendor=vendor, amount=amount)

    order.vendor_credit_processed = True


def reduce_stock_for_paid_order(order):
    if order.stock_deducted:
        return

    for item in order.items.select_related('product__vendor').all():
        product = item.product
        quantity_to_deduct = min(product.stock, item.quantity)
        product.stock = product.stock - quantity_to_deduct
        product.save(update_fields=['stock'])

        if product.stock <= product.low_stock_threshold:
            Notification.objects.create(
                user=product.vendor,
                message=f"Low stock alert: {product.name} has {product.stock} item(s) left.",
                link="#"
            )

    order.stock_deducted = True
