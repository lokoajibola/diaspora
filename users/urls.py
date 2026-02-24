from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor/kyc/', views.vendor_kyc, name='vendor_kyc'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('notifications/', views.vendor_notifications, name='vendor_notifications'),
    path('logistics-dashboard/', views.logistics_dashboard, name='logistics_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Also add the status update URL we talked about earlier
    path('admin/order/<int:order_id>/update-status/', views.admin_update_status, name='admin_update_status'),
    path('update-order-status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),
]