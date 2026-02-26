from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.vendor_dashboard, name='products_vendor_dashboard'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:product_id>/images/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),
    path('vendor/<int:vendor_id>/', views.vendor_store, name='vendor_store'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
]