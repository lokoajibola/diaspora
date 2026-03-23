from django.urls import path
from . import views

urlpatterns = [
    path('admin/payouts/', views.admin_payout_dashboard, name='payments_admin_payout_dashboard'),
    path('admin/payouts/pay/<int:payout_id>/', views.mark_as_paid, name='mark_as_paid'),
]