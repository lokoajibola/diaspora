from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('track/<int:order_id>/', views.track_order, name='track_order'),
    
    path('verify/', views.verify_paystack_payment, name='verify_payment'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('webhook/paystack/', views.paystack_webhook, name='paystack_webhook'),
    path('my-orders/', views.order_history, name='order_history'),

    path('vendor/dispatch/<int:order_id>/', views.vendor_confirm_dispatch, name='vendor_confirm_dispatch'),
    path('my-orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    
]