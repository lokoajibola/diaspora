from django.shortcuts import redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from .forms import CustomerRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from orders.models import Order
from django.db.models import Sum, F
from orders.models import OrderItem
from products.models import Product

@login_required
def vendor_dashboard(request):
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