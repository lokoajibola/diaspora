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

def track_order(request, order_id):
    # Customers can only see their own orders
    if request.user.role == 'customer':
        order = get_object_or_404(Order, id=order_id, customer=request.user)
    else:
        # Admins or Logistics can see any order
        order = get_object_or_404(Order, id=order_id)
        
    return render(request, 'orders/track_order.html', {'order': order})

def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product)
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'orders/cart_detail.html', {'cart': cart})

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

def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('home')

    shipping_rates = settings.SHIPPING_RATES
    # Get country from URL or default to UK
    selected_country = request.GET.get('country', 'UK')
    shipping_fee = shipping_rates.get(selected_country, 0)

    if request.method == 'POST':
        # Match these names exactly to your <input name="..."> in checkout.html
        receiver_name = request.POST.get('receiver_name')
        receiver_phone = request.POST.get('receiver_phone')
        delivery_address = request.POST.get('delivery_address') # Ensure this matches HTML
        
        # 2. Calculate Totals
        subtotal = cart.get_total_price()
        total_price = float(subtotal) + float(shipping_fee)
        
        # 3. Create Order
        order = Order.objects.create(
            customer=request.user, # Use 'customer' here if that's what is in models.py
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            delivery_address=delivery_address,
            country=selected_country,
            shipping_fee=shipping_fee,
            total_amount=total_price,
            status='pending'
        )

        # 4. Create Order Items (Linking Products to Order)
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                price=item['price'],
                quantity=item['quantity']
            )

        # 5. Clear Cart and Redirect to Payment
        request.session['order_id'] = order.id
        return redirect('process_payment') # Next step: Paystack redirect

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