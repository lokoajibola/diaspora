from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Category
from .forms import ProductForm
from django.db.models import Q
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .forms import ProductForm
from django.utils import timezone


@login_required
def promote_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, vendor=request.user)
    promotion_fee = 5000  # Example: 5000 Naira/Cedis
    
    # Initialize Paystack
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "email": request.user.email,
        "amount": promotion_fee * 100, # Amount in Kobo
        "callback_url": request.build_absolute_uri(reverse('promote_callback')),
        "metadata": {
            "product_id": product.id,
            "type": "promotion"
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    res_data = response.json()
    
    if res_data['status']:
        return redirect(res_data['data']['authorization_url'])
    else:
        messages.error(request, "Could not initialize payment.")
        return redirect('vendor_dashboard')


def promote_callback(request):
    reference = request.GET.get('reference')
    # Verify transaction with Paystack API...
    # (Assuming verification is successful)
    
    # Get product_id from metadata sent earlier
    # For simplicity in this snippet, we'll assume we got the product
    product_id = request.session.get('pending_promotion_id') 
    product = Product.objects.get(id=product_id)
    
    product.is_promoted = True
    product.promotion_expires_at = timezone.now() + timedelta(days=7)
    product.save()
    
    messages.success(request, f"{product.name} is now promoted on the homepage!")
    return redirect('vendor_dashboard')

@login_required
def vendor_dashboard(request):
    if request.user.role != 'vendor':
        return redirect('home')
    
    products = Product.objects.filter(vendor=request.user)
    return render(request, 'products/vendor_dashboard.html', {'products': products})


@login_required
def add_product(request):
    if request.user.role != 'vendor':
        return redirect('home')
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES) # FILES is required for images
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user # Automatically assign the vendor
            product.save()
            return redirect('vendor_dashboard')
    else:
        form = ProductForm()
    
    return render(request, 'products/add_product.html', {'form': form})

def product_list(request):
    products = Product.objects.filter(is_active=True)
    # Basic currency conversion example (Static rate for now)
    exchange_rate = 1800  # 1 GBP = 1800 NGN
    return render(request, 'products/product_list.html', {
        'products': products,
        'rate': exchange_rate
    })
    
def set_currency(request):
    currency = request.GET.get('currency', 'NGN')
    if currency in ['NGN', 'GBP', 'USD']:
        request.session['currency'] = currency
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def home(request):
    products = Product.objects.filter(is_active=True)
    # Fetch only products with active promotions
    promoted_products = Product.objects.filter(
        is_promoted=True, 
        promotion_expires_at__gt=timezone.now()
    )[:5] # Limit to top 5
    
    # Filter by Category
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    query = request.GET.get('q')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        )
    else:
        products = Product.objects.filter(is_active=True)
    
    # Sorting Logic
    sort = request.GET.get('sort', '-created_at') # Default to newest
    products = products.order_by(sort)
    
    categories = Category.objects.all()
    return render(request, 'home.html', {'products': products, 'categories': categories, 'promoted_products': promoted_products, 'query': query})
   
def vendor_store(request, vendor_id):
    vendor_products = Product.objects.filter(vendor_id=vendor_id, is_active=True)
    return render(request, 'products/vendor_store.html', {'products': vendor_products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})