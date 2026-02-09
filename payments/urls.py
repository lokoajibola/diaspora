from django.urls import path
from . import views

urlpatterns = [
    # Ensure the 'name' matches exactly what your template is looking for
    path('admin/payouts/', views.admin_payout_dashboard, name='admin_dashboard'),
    path('admin/payouts/pay/<int:payout_id>/', views.mark_as_paid, name='mark_as_paid'),
]