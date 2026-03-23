from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.db import models

from orders.cart import Cart
from .models import VendorPayout
from django.utils import timezone

@staff_member_required
def admin_payout_dashboard(request):
    pending_payouts = VendorPayout.objects.filter(is_paid=False)
    paid_payouts = VendorPayout.objects.filter(is_paid=True).order_by('-payout_date')[:10]
    
    return render(request, 'admin/payout_dashboard.html', {
        'pending_payouts': pending_payouts,
        'paid_payouts': paid_payouts
    })

@staff_member_required
def mark_as_paid(request, payout_id):
    payout = VendorPayout.objects.get(id=payout_id)
    payout.is_paid = True
    payout.payout_date = timezone.now()
    payout.save()
    return redirect('payments_admin_payout_dashboard')

  
@staff_member_required
def admin_payout_summary(request):
    total_to_pay = VendorPayout.objects.filter(is_paid=False).aggregate(models.Sum('amount_owed'))
    return render(request, 'admin/payout_summary.html', {
        'total_pending': total_to_pay['amount_owed__sum'] or 0
    })