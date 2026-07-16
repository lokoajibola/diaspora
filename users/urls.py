from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('vendor/dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor/kyc/', views.vendor_kyc, name='vendor_kyc'),
    path('vendor/kyc/dashboard/', views.vendor_kyc_dashboard, name='vendor_kyc_dashboard'),
    path('vendor/kyc/<str:step>/', views.vendor_kyc_step, name='vendor_kyc_step'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('notifications/', views.vendor_notifications, name='vendor_notifications'),
    path('logistics-dashboard/', views.logistics_dashboard, name='logistics_dashboard'),
    path('admin/vendors/<int:user_id>/approve-kyc/', views.admin_approve_vendor_kyc, name='admin_approve_vendor_kyc'),
    path('admin/vendors/<int:user_id>/reject-kyc/', views.admin_reject_vendor_kyc, name='admin_reject_vendor_kyc'),
    path('admin/users/<int:user_id>/update/', views.admin_update_user, name='admin_update_user'),
    path('update-order-status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),
    # OTP Verification URLs
    path('otp/request/<str:otp_type>/', views.otp_request, name='otp_request'),
    path('otp/verify/<str:otp_type>/', views.otp_verify_page, name='otp_verify'),
    path('otp/verify/<str:otp_type>/submit/', views.otp_verify_submit, name='otp_verify_submit'),
    
    # New KYC Review URLs
    path('admin/kyc/review/', views.admin_kyc_review_list, name='admin_kyc_review_list'),
    path('admin/kyc/review/<int:user_id>/', views.admin_kyc_review_detail, name='admin_kyc_review_detail'),
    path('admin/kyc/review/<int:user_id>/checks/', views.admin_kyc_perform_checks, name='admin_kyc_perform_checks'),
    path('admin/kyc/review/<int:user_id>/qa/', views.admin_qa_review, name='admin_qa_review'),
    path('admin/kyc/review/<int:user_id>/verified-seller/', views.admin_verified_seller, name='admin_verified_seller'),
]
