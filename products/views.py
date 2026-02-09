from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Category
from .forms import ProductForm
from django.db.models import Q

@login_required
def vendor_dashboard(request):
    if request.user.role != 'vendor':
        return redirect('home')
    
    products = Product.objects.filter(vendor=request.user)
    return render(request, 'products/vendor_dashboard.html', {'products': products})

from django.contrib.auth.decorators import login_required
from .forms import ProductForm

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
    
    categories = Category.objects.all()
    return render(request, 'home.html', {'products': products, 'categories': categories, 'query': query})
   
def vendor_store(request, vendor_id):
    vendor_products = Product.objects.filter(vendor_id=vendor_id, is_active=True)
    return render(request, 'products/vendor_store.html', {'products': vendor_products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})