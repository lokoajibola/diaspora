from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from .cart import Cart
from payments.utils import initialize_paystack_payment
import requests
from django.conf import settings
from .models import Order, OrderItem
from django.contrib.auth.decorators import login_required
from payments.models import VendorPayout
import json
import hmac
import hashlib
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from users.models import Notification
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.core.exceptions import PermissionDenied
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
@login_required
def update_cart_ajax(request):
    """AJAX view to update cart quantities"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be at least 1'
            })
        
        # Get cart from session
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            cart[product_id_str]['quantity'] = quantity
            request.session['cart'] = cart
            request.session.modified = True
            
            # Calculate new total for this item
            item = cart[product_id_str]
            item_total = float(item['price']) * quantity
            
            return JsonResponse({
                'success': True,
                'message': 'Quantity updated',
                'item_total': item_total,
                'quantity': quantity
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Item not found in cart'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def can_view_order(user, order):
    """Check if user can view a specific order."""
    if user.is_staff or user.is_superuser:
        return True
    if hasattr(user, 'role') and user.role in ['admin', 'logistics', 'vendor']:
        return True
    if order.customer == user:
        return True
    return False

def payment_verify(request):
    # ... after verifying payment is successful ...
    order.status = 'paid'
    order.save()

    # Alert the vendors involved
    for item in order.items.all():
        vendor = item.product.vendor
        Notification.objects.create(
            user=vendor,
            message=f"New Sale! {item.quantity}x {item.product.name} has been ordered.",
            link=reverse('vendor_dashboard')
        )

@staff_member_required
def admin_update_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.status = request.POST.get('status')
        order.save()
        messages.success(request, f"Order #{order_id} status updated!")
    return redirect('admin_dashboard')

@login_required
def vendor_confirm_dispatch(request, order_id):
    # Ensure the user is a vendor and the order exists
    if request.user.role != 'vendor':
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        # 1. Update status
        order.status = 'shipped'
        
        # 2. Generate a Tracking Number if one doesn't exist
        if not order.tracking_number:
            # Generates a code like DW-ABC12345
            short_id = str(uuid.uuid4()).upper()[:8]
            order.tracking_number = f"DW-{short_id}"
        
        order.save()
        
        messages.success(request, f"Order #{order.id} marked as Dispatched! Tracking: {order.tracking_number}")
        return redirect('vendor_dashboard')

    return redirect('vendor_dashboard')

@csrf_exempt
def paystack_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
    
    # Verify the request actually came from Paystack
    hash = hmac.new(settings.PAYSTACK_SECRET_KEY.encode('utf-8'), payload, hashlib.sha512).hexdigest()
    
    if hash == sig_header:
        data = json.loads(payload)
        if data['event'] == 'charge.success':
            ref = data['data']['reference']
            # Find the order and mark as paid
            try:
                order = Order.objects.get(paystack_ref=ref)
                order.status = 'paid' # Or your relevant status
                order.save()
            except Order.DoesNotExist:
                pass
                
    return HttpResponse(status=200)

from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.core.exceptions import PermissionDenied

def can_view_order(user, order):
    """Check if user can view a specific order."""
    if user.is_staff or user.is_superuser:
        return True
    if hasattr(user, 'role') and user.role in ['admin', 'logistics', 'vendor']:
        return True
    if order.customer == user:
        return True
    return False

@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if not can_view_order(request.user, order):
        raise PermissionDenied("You don't have permission to view this order")
    
    return render(request, 'orders/track_order.html', {'order': order})

def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    # Get quantity from form, default to 1
    quantity = int(request.POST.get('quantity', 1))
    # Get the override flag (True if updating from cart, False if adding from shop)
    override = request.POST.get('override', 'False') == 'True'
    
    cart.add(product=product, quantity=quantity, override_quantity=override)
    
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'orders/cart_detail.html', {'cart': cart})

@require_POST
def cart_update(request):
    # Handle both JSON and form data
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = data.get('quantity')
    else:
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')

    if not product_id or not quantity:
        messages.error(request, 'Missing product or quantity.')
        return redirect('cart_detail')

    try:
        quantity = int(quantity)
        if quantity < 1:
            quantity = 1
    except ValueError:
        messages.error(request, 'Invalid quantity.')
        return redirect('cart_detail')

    # Get cart from session
    cart = request.session.get('cart', {})

    product_id_str = str(product_id)

    if product_id_str in cart:
        # Update quantity
        cart[product_id_str]['quantity'] = quantity
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Cart updated successfully.')
    else:
        messages.error(request, 'Product not found in your cart.')

    # If AJAX, return JSON
    if request.content_type == 'application/json':
        return JsonResponse({'success': True})
    else:
        return redirect('cart_detail')
        
@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'orders/order_detail_view.html', {'order': order})

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')

def process_payment(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id)
    
    # Paystack requires amount in Kobo (NGN * 100)
    paystack_amount = int(order.total_amount * 100)
    
    context = {
        'order': order,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        'paystack_amount': paystack_amount,
        'email': request.user.email,
    }
    return render(request, 'orders/payment.html', context)

@login_required
def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('home')

    shipping_rates = settings.SHIPPING_RATES
    selected_country = request.GET.get('country', 'UK')
    # Convert shipping fee to float immediately
    shipping_fee = float(shipping_rates.get(selected_country, 0))

    if request.method == 'POST':
        receiver_name = request.POST.get('receiver_name')
        receiver_phone = request.POST.get('receiver_phone')
        delivery_address = request.POST.get('delivery_address') 
        
        # 2. Calculate Totals (Ensuring we use floats for the database/session)
        subtotal = float(cart.get_total_price())
        total_price = subtotal + shipping_fee
        
        # 3. Create Order
        order = Order.objects.create(
            customer=request.user,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            delivery_address=delivery_address,
            country=selected_country,
            shipping_fee=shipping_fee,
            total_amount=total_price,
            status='pending'
        )

        # 4. Create Order Items
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                # item['price'] might be a Decimal, database handles this fine
                price=item['price'], 
                quantity=item['quantity']
            )

        # 5. Clear Cart and Redirect
        cart.clear() # This removes the Decimals from the session
        
        request.session['order_id'] = int(order.id)
        # Store amount as string to be 100% safe for Paystack later
        request.session['payment_amount'] = str(total_price) 
        
        return redirect('process_payment')

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'shipping_rates': shipping_rates,
        'selected_country': selected_country,
        'shipping_fee': shipping_fee
    })
    
def payment_success(request):
    reference = request.GET.get('reference')
    # Optional: You can verify the reference with Paystack API here
    
    # Clear the cart from session
    if 'cart' in request.session:
        del request.session['cart']
        
    return render(request, 'orders/success.html', {'reference': reference})

def verify_paystack_payment(request):
    reference = request.GET.get('reference')
    url = f"https://api.api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    
    response = requests.get(url, headers=headers)
    res_data = response.json()

    from payments.models import VendorPayout
    cart = Cart(request)
    
    # Inside the verification success logic:
    for item in cart:
        VendorPayout.objects.create(
            vendor=item.product.vendor,
            amount_owed=item.product.base_price * item.quantity
        )
    
    if res_data['status'] and res_data['data']['status'] == 'success':
        # Find order using reference (assuming you stored ref in order)
        # For simplicity in this logic, we use session or latest order
        order = Order.objects.filter(customer=request.user).latest('created_at')
        order.paystack_ref = reference
        order.status = 'processing'
        order.save()

        # Generate Payouts for Vendors involved
        # Assuming an OrderItem model exists to track specific products
        # Logic: amount = item.product.base_price
        # VendorPayout.objects.create(vendor=..., amount_owed=...)

        return render(request, 'orders/success.html', {'order': order})
    
    return render(request, 'orders/failure.html')