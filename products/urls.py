from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('product/add/', views.add_product, name='add_product'),
    path('vendor/<int:vendor_id>/', views.vendor_store, name='vendor_store'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
]