from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ProductForm
from .models import Category, Product, ProductImage


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
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user
            product.country = getattr(request.user, 'country', Product.CountryChoices.NIGERIA)
            product.save()

            for image in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(product=product, image=image)

            return redirect('vendor_dashboard')
    else:
        form = ProductForm()

    return render(request, 'products/add_product.html', {'form': form})


@login_required
def edit_product(request, product_id):
    if request.user.role != 'vendor':
        return redirect('home')

    product = get_object_or_404(Product, id=product_id, vendor=request.user)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()

            for image in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(product=product, image=image)

            return redirect('vendor_dashboard')
    else:
        form = ProductForm(instance=product)

    gallery_images = product.images.all().order_by('created_at')
    return render(
        request,
        'products/edit_product.html',
        {
            'form': form,
            'product': product,
            'gallery_images': gallery_images,
        },
    )


@login_required
def delete_product_image(request, product_id, image_id):
    if request.user.role != 'vendor':
        return redirect('home')

    product = get_object_or_404(Product, id=product_id, vendor=request.user)
    image = get_object_or_404(ProductImage, id=image_id, product=product)

    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Product image deleted.')

    return redirect('edit_product', product_id=product.id)


def product_list(request):
    country = request.GET.get('country')
    products = Product.objects.filter(is_active=True)
    if country in [Product.CountryChoices.NIGERIA, Product.CountryChoices.GHANA]:
        products = products.filter(country=country)

    exchange_rate = 1800
    return render(
        request,
        'products/product_list.html',
        {
            'products': products,
            'rate': exchange_rate,
            'selected_country': country,
        },
    )


def set_currency(request):
    currency = request.POST.get('currency') or request.GET.get('currency', 'NGN')
    if currency in settings.CURRENCIES:
        request.session['currency'] = currency

    next_url = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER')
    return redirect(next_url or 'home')


def home(request):
    query = request.GET.get('q')
    category_slug = request.GET.get('category')
    country = request.GET.get('country')
    sort_by = request.GET.get('sort', 'latest')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    selected_currency_code = request.session.get('currency', 'NGN')
    conversion_rate = Decimal(str(settings.EXCHANGE_RATES.get(selected_currency_code, 1.0)))

    products = Product.objects.filter(is_active=True).select_related('vendor', 'category')

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if country in [Product.CountryChoices.NIGERIA, Product.CountryChoices.GHANA]:
        products = products.filter(country=country)

    if min_price:
        try:
            min_price_ngn = Decimal(str(min_price)) / conversion_rate
            products = products.filter(base_price__gte=min_price_ngn)
        except (TypeError, ValueError, InvalidOperation, ZeroDivisionError):
            pass

    if max_price:
        try:
            max_price_ngn = Decimal(str(max_price)) / conversion_rate
            products = products.filter(base_price__lte=max_price_ngn)
        except (TypeError, ValueError, InvalidOperation, ZeroDivisionError):
            pass

    sort_map = {
        'latest': '-created_at',
        '-created_at': '-created_at',
        'oldest': 'created_at',
        'created_at': 'created_at',
        'price_low': 'base_price',
        'base_price': 'base_price',
        'price_high': '-base_price',
        '-base_price': '-base_price',
        'name_asc': 'name',
        'name': 'name',
        'name_desc': '-name',
        '-name': '-name',
    }
    products = products.order_by(sort_map.get(sort_by, '-created_at'))

    promoted_products = Product.objects.filter(
        is_active=True,
        is_promoted=True,
        promotion_expires_at__gt=timezone.now(),
    )[:5]

    categories = Category.objects.annotate(
        active_product_count=Count('product', filter=Q(product__is_active=True))
    ).order_by('name')

    return render(
        request,
        'home.html',
        {
            'products': products,
            'promoted_products': promoted_products,
            'categories': categories,
            'query': query,
            'selected_category': category_slug,
            'selected_country': country,
            'sort_by': sort_by,
            'min_price': min_price,
            'max_price': max_price,
        },
    )


def vendor_store(request, vendor_id):
    vendor_products = Product.objects.filter(vendor_id=vendor_id, is_active=True)
    return render(request, 'products/vendor_store.html', {'products': vendor_products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    gallery_images = product.images.all().order_by('created_at')
    return render(
        request,
        'products/product_detail.html',
        {
            'product': product,
            'gallery_images': gallery_images,
        },
    )
