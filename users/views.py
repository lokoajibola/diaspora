from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomerRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from orders.models import Order
from django.db.models import Sum, F
from orders.models import OrderItem, PayoutRequest
from products.models import Product
from .models import User, Notification
from django.utils import timezone
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from orders.utils import ensure_tracking_number, credit_vendors_for_paid_order, reduce_stock_for_paid_order

@staff_member_required
def approve_payout(request, payout_id):
    if request.method == 'POST':
        payout = get_object_or_404(PayoutRequest, id=payout_id)
        transfer_reference = request.POST.get('transfer_reference', '').strip()
        
        if not payout.is_paid:
            with transaction.atomic():
                vendor = payout.vendor
                if not vendor.bank_name or not vendor.bank_account_name or not vendor.bank_account_number:
                    messages.error(request, "Vendor bank details are missing. Ask vendor to complete KYC bank details first.")
                    return redirect('admin_dashboard')

                if not transfer_reference:
                    messages.error(request, "Transfer reference is required to confirm payout.")
                    return redirect('admin_dashboard')

                if vendor.balance >= payout.amount:
                    vendor.balance -= payout.amount
                    vendor.save()
                    
                    payout.is_paid = True
                    payout.transfer_reference = transfer_reference
                    payout.paid_at = timezone.now()
                    payout.processed_by = request.user
                    payout.save()
                    
                    messages.success(request, f"Payout of {payout.amount} for {vendor.shop_name} marked as transferred.")
                else:
                    messages.error(request, "Vendor balance is insufficient for this payout amount.")
            
                Notification.objects.create(
                    user=vendor,
                    message=f"Your payout request of {payout.amount} has been transferred to your bank account.",
                    link="#"
                )
        
        else:
            messages.info(request, "This payout has already been processed.")
    
    

    return redirect('admin_dashboard')

@staff_member_required # Ensures only site admins can access
def admin_dashboard(request):
    total_revenue = Order.objects.filter(status__in=['paid', 'shipped', 'delivered']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_vendors = User.objects.filter(role='vendor').count()
    total_customers = User.objects.filter(role='customer').count()
    total_logistics = User.objects.filter(role='logistics').count()
    
    query = request.GET.get('q', '')
    all_orders = Order.objects.all().select_related('customer')
    
    if query:
        all_orders = all_orders.filter(
            Q(id__icontains=query) | 
            Q(receiver_name__icontains=query) | 
            Q(delivery_address__icontains=query) |
            Q(customer__phone_number__icontains=query)
        )

    thirty_days_ago = timezone.now() - timedelta(days=30)
    revenue_data = (
        Order.objects.filter(status='paid', created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(daily_revenue=Sum('total_amount'))
        .order_by('date')
    )

    chart_labels = [data['date'].strftime('%b %d') for data in revenue_data]
    chart_values = [float(data['daily_revenue']) for data in revenue_data]

    payout_requests = PayoutRequest.objects.filter(is_paid=False).select_related('vendor').order_by('-created_at')
    recent_transfers = PayoutRequest.objects.filter(is_paid=True).select_related('vendor', 'processed_by').order_by('-paid_at')[:10]

    pending_payout_total = User.objects.filter(role='vendor').aggregate(Sum('balance'))['balance__sum'] or 0
    transferred_total = PayoutRequest.objects.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0

    managed_users = User.objects.filter(is_superuser=False).order_by('-date_joined')[:20]
    pending_kyc_vendors = User.objects.filter(
        role='vendor',
        is_verified=False
    ).filter(
        Q(kyc_rejection_reason__isnull=True) | Q(kyc_rejection_reason='')
    ).order_by('-date_joined')[:10]
    delivery_queue = Order.objects.filter(status__in=['paid', 'shipped']).order_by('-created_at')[:20]

    context = {
        'revenue': total_revenue,
        'order_count': total_orders,
        'vendor_count': total_vendors,
        'customer_count': total_customers,
        'logistics_count': total_logistics,
        'orders': all_orders,
        'query': query,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'payout_requests': payout_requests,
        'recent_transfers': recent_transfers,
        'pending_payout_total': pending_payout_total,
        'transferred_total': transferred_total,
        'managed_users': managed_users,
        'pending_kyc_vendors': pending_kyc_vendors,
        'pending_kyc_count': pending_kyc_vendors.count(),
        'delivery_queue': delivery_queue,
    }
    return render(request, 'admin_custom/dashboard.html', context)

@staff_member_required
def admin_approve_vendor_kyc(request, user_id):
    if request.method == 'POST':
        vendor = get_object_or_404(User, id=user_id, role='vendor')
        vendor.is_verified = True
        vendor.kyc_rejection_reason = None
        vendor.save(update_fields=['is_verified', 'kyc_rejection_reason'])

        Notification.objects.create(
            user=vendor,
            message="Your KYC has been approved. Your vendor account is now verified.",
            link="#"
        )
        messages.success(request, f"Vendor {vendor.phone_number} KYC approved.")

    return redirect('admin_dashboard')

@staff_member_required
def admin_reject_vendor_kyc(request, user_id):
    if request.method == 'POST':
        vendor = get_object_or_404(User, id=user_id, role='vendor')
        rejection_reason = request.POST.get('rejection_reason', '').strip()

        if not rejection_reason:
            messages.error(request, "Rejection reason is required.")
            return redirect('admin_dashboard')

        vendor.is_verified = False
        vendor.kyc_rejection_reason = rejection_reason
        vendor.save(update_fields=['is_verified', 'kyc_rejection_reason'])

        Notification.objects.create(
            user=vendor,
            message=f"Your KYC was rejected. Reason: {rejection_reason}",
            link="#"
        )
        messages.info(request, f"Vendor {vendor.phone_number} KYC rejected.")

    return redirect('admin_dashboard')

@staff_member_required
def admin_update_user(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        is_verified = request.POST.get('is_verified') == 'on'

        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if role in valid_roles:
            target_user.role = role

        target_user.is_active = is_active
        target_user.is_verified = is_verified
        target_user.save()
        messages.success(request, f"User {target_user.phone_number} updated.")

    return redirect('admin_dashboard')

@staff_member_required
def admin_update_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        # Validation to ensure the status is one of our choices
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status in valid_statuses:
            order.status = new_status

            if new_status == 'paid':
                ensure_tracking_number(order)

            order.save()

            if new_status == 'paid':
                credit_vendors_for_paid_order(order)
                reduce_stock_for_paid_order(order)
                order.save(update_fields=['vendor_credit_processed', 'stock_deducted'])

            messages.success(request, f"Order #{order.id} updated to {order.get_status_display()}.")
        else:
            messages.error(request, "Invalid status selected.")
            
    return redirect('admin_dashboard')

@login_required
def vendor_notifications(request):
    notifications = request.user.notifications.all()
    # Mark all as read when they visit this page
    notifications.update(is_read=True)
    return render(request, 'users/notifications.html', {'notifications': notifications})

@login_required
def vendor_dashboard(request):
    if request.user.role != 'vendor':
        return redirect('home')

    my_products = Product.objects.filter(vendor=request.user)

    vendor_sales = OrderItem.objects.filter(
        product__vendor=request.user,
        order__status__in=['paid', 'shipped', 'delivered']
    ).select_related('order', 'product')

    vendor_orders = (
        Order.objects
        .filter(items__product__vendor=request.user, status__in=['paid', 'shipped', 'delivered'])
        .select_related('customer')
        .distinct()
        .order_by('-created_at')
    )

    total_revenue = vendor_sales.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or 0

    active_orders_count = vendor_orders.filter(status__in=['paid', 'shipped']).count()
    low_stock_products = my_products.filter(stock__lte=F('low_stock_threshold')).order_by('stock')
    has_kyc_details = all([
        request.user.shop_name,
        request.user.shop_address,
        request.user.bank_name,
        request.user.bank_account_name,
        request.user.bank_account_number,
        request.user.id_document,
    ])

    context = {
        'products': my_products,
        'sales': vendor_sales,
        'sold_items': vendor_sales.order_by('-order__created_at'),
        'total_revenue': total_revenue,
        'orders': vendor_orders,
        'active_orders_count': active_orders_count,
        'total_products_count': my_products.count(),
        'paid_orders_count': vendor_orders.filter(status='paid').count(),
        'total_stock_quantity': my_products.aggregate(total=Sum('stock'))['total'] or 0,
        'low_stock_products': low_stock_products,
        'has_kyc_details': has_kyc_details,
    }
    return render(request, 'users/vendor_dashboard.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        return redirect('home')
    return render(request, 'registration/edit_profile.html')

@login_required
def logistics_dashboard(request):
    if request.user.role != 'logistics' and not request.user.is_staff:
        return redirect('home')
    
    # Show orders that need attention
    pending_shipments = Order.objects.filter(status__in=['paid', 'shipped']).order_by('-created_at')
    return render(request, 'users/logistics_dashboard.html', {'orders': pending_shipments})

@login_required
def update_order_status(request, order_id, new_status):
    if request.user.role == 'logistics' or request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()
    return redirect('logistics_dashboard')

@login_required
def request_payout(request):
    if request.user.role != 'vendor':
        return redirect('home')

    if not request.user.bank_name or not request.user.bank_account_name or not request.user.bank_account_number:
        messages.error(request, "Please complete your bank details in KYC before requesting payout.")
        return redirect('vendor_kyc')

    if request.user.balance > 0:
        PayoutRequest.objects.create(
            vendor=request.user,
            amount=request.user.balance
        )
        # Optionally reset balance to 0 immediately or wait until Admin approves
        messages.success(request, "Payout request submitted! Admin will review it shortly.")
    else:
        messages.error(request, "Your balance is 0.00.")

    return redirect('vendor_dashboard')

@login_required
def vendor_kyc(request):
    if request.user.role != 'vendor':
        return redirect('home')
        
    if request.method == 'POST':
        # Updating the user instance directly
        user = request.user
        user.shop_name = request.POST.get('shop_name')
        user.shop_address = request.POST.get('shop_address')
        user.bank_name = request.POST.get('bank_name')
        user.bank_account_name = request.POST.get('bank_account_name')
        user.bank_account_number = request.POST.get('bank_account_number')
        user.kyc_rejection_reason = None
        
        if 'id_document' in request.FILES:
            user.id_document = request.FILES['id_document']
            
        user.save()
        messages.success(request, "KYC and bank details submitted for review!")
        return redirect('vendor_dashboard')
        
    return render(request, 'users/kyc_form.html')

def register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! You can now login.")
            return redirect('login')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def role_based_redirect(request):
    user = request.user
    if user.is_staff or user.role == 'admin':
        return redirect('/admin/')
    elif user.role == 'vendor':
        return redirect('vendor_dashboard')
    elif user.role == 'logistics':
        return redirect('logistics_dashboard')
    else:
        return redirect('home')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.role == 'admin' or user.is_superuser:
            return reverse_lazy('admin_dashboard')
        elif user.role == 'vendor':
            return reverse_lazy('vendor_dashboard')
        elif user.role == 'logistics':
            return reverse_lazy('logistics_dashboard')
        else:
            # Customers go to the home page or order tracking
            return reverse_lazy('home')