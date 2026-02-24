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
from .models import User
from django.utils import timezone
from django.db.models.functions import TruncDate
from datetime import timedelta
import uuid
from django.db import transaction
from django.db.models import Q

@staff_member_required
def approve_payout(request, payout_id):
    if request.method == 'POST':
        payout = get_object_or_404(PayoutRequest, id=payout_id)
        
        if not payout.is_paid:
            with transaction.atomic():
                # 1. Update the vendor's balance
                vendor = payout.vendor
                if vendor.balance >= payout.amount:
                    vendor.balance -= payout.amount
                    vendor.save()
                    
                    # 2. Mark the request as paid
                    payout.is_paid = True
                    payout.save()
                    
                    messages.success(request, f"Payout of ${payout.amount} for {vendor.shop_name} confirmed.")
                else:
                    messages.error(request, "Vendor balance is insufficient for this payout amount.")
            
                # Add this notification logic
                Notification.objects.create(
                    user=vendor,
                    message=f"Your payout request of ${payout.amount} has been processed and paid!",
                    link="#" # Or link to a payout history page
                )
        
        else:
            messages.info(request, "This payout has already been processed.")
    
    

    return redirect('admin_dashboard')

@staff_member_required # Ensures only site admins can access
def admin_dashboard(request):
    # 1. Analytics Calculations
    total_revenue = Order.objects.filter(status__in=['paid', 'shipped', 'delivered']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_vendors = User.objects.filter(role='vendor').count()
    total_customers = User.objects.filter(role='customer').count()
    
    # 2. Search & Order Tracking
    query = request.GET.get('q', '')
    all_orders = Order.objects.all().select_related('customer')
    
    if query:
        all_orders = all_orders.filter(
            Q(id__icontains=query) | 
            Q(receiver_name__icontains=query) | 
            Q(delivery_address__icontains=query) |
            Q(customer__phone_number__icontains=query)
        )

    # --- Chart Data: Revenue over the last 30 days ---
    thirty_days_ago = timezone.now() - timedelta(days=30)
    revenue_data = (
        Order.objects.filter(status='paid', created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(daily_revenue=Sum('total_amount'))
        .order_by('date')
    )

    # Prepare labels and values for JavaScript
    chart_labels = [data['date'].strftime('%b %d') for data in revenue_data]
    chart_values = [float(data['daily_revenue']) for data in revenue_data]
    payout_requests = PayoutRequest.objects.filter(is_paid=False).order_by('-created_at')

    context = {
        'revenue': total_revenue,
        'order_count': total_orders,
        'vendor_count': total_vendors,
        'customer_count': total_customers,
        'orders': all_orders,
        'query': query,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'payout_requests': payout_requests,
    }
    return render(request, 'admin_custom/dashboard.html', context)

@staff_member_required
def admin_update_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        # Validation to ensure the status is one of our choices
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status in valid_statuses:
            order.status = new_status
            order.save()
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
    all_orders = Order.objects.all().select_related('customer')

    # Ensure only vendors can access this
    if request.user.role != 'vendor':
        return redirect('home')
    
    # 1. Get all products belonging to this vendor
    my_products = Product.objects.filter(vendor=request.user)
    
    # 2. Get all OrderItems for these products (where payment is successful)
    vendor_sales = OrderItem.objects.filter(
        product__vendor=request.user,
        order__status__in=['paid', 'shipped', 'delivered']
    ).select_related('order', 'product')

    # 3. Calculate Total Revenue (Price * Quantity)
    total_revenue = vendor_sales.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or 0

    context = {
        'products': my_products,
        'sales': vendor_sales,
        'total_revenue': total_revenue,
        'orders': all_orders,
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
        
        if 'id_document' in request.FILES:
            user.id_document = request.FILES['id_document']
            
        user.save()
        messages.success(request, "KYC Details submitted for review!")
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