from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logistics-dashboard/', views.logistics_dashboard, name='logistics_dashboard'),
    path('update-order-status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),
]