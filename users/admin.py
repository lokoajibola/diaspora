from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Guarantor, ProductCompliance, KYCInternalCheck, ShopPhoto, QualityAssurance, VendorPerformance, VerifiedSellerStatus


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['phone_number', 'role', 'country', 'kyc_stage', 'is_staff', 'is_active']
    list_filter = ['role', 'country', 'kyc_stage', 'is_staff', 'is_active']
    
    # This fixes the "Unknown field username" error
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'country', 'date_of_birth', 'nationality')}),
        ('Business Info', {'fields': ('shop_name', 'shop_address', 'business_registration_number', 'business_type', 'business_start_date', 'business_description', 'tin', 'business_logo')}),
        ('Identity', {'fields': ('nin', 'bvn', 'id_document_type', 'id_document', 'liveness_selfie', 'passport_photo')}),
        ('Contact', {'fields': ('whatsapp_number', 'emergency_contact_name', 'emergency_contact_phone', 'home_address', 'utility_bill')}),
        ('Banking', {'fields': ('bank_name', 'bank_account_name', 'bank_account_number')}),
        ('KYC Status', {'fields': ('kyc_stage', 'kyc_submitted_at', 'kyc_approved_at', 'kyc_rejection_reason', 'otp_phone_verified', 'otp_email_verified', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Role Information', {'fields': ('role', 'balance')}),
    )
    
    # This fixes the error when clicking "Add User"
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password', 'role', 'country', 'is_staff', 'is_active'),
        }),
    )
    
    search_fields = ('phone_number', 'shop_name', 'first_name', 'last_name')
    ordering = ('phone_number',)


@admin.register(Guarantor)
class GuarantorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'vendor', 'phone_number', 'relationship', 'created_at']
    search_fields = ['full_name', 'vendor__phone_number']


@admin.register(ProductCompliance)
class ProductComplianceAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'nafdac_number', 'son_number', 'is_verified', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['vendor__phone_number', 'nafdac_number']


@admin.register(KYCInternalCheck)
class KYCInternalCheckAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'overall_status', 'nin_verified', 'bvn_verified', 'bank_matched', 'checked_by', 'checked_at']
    list_filter = ['overall_status']
    search_fields = ['vendor__phone_number']


@admin.register(ShopPhoto)
class ShopPhotoAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'created_at']
    search_fields = ['vendor__phone_number']


@admin.register(QualityAssurance)
class QualityAssuranceAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'status', 'qa_officer', 'qa_date']
    list_filter = ['status']


@admin.register(VendorPerformance)
class VendorPerformanceAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'acceptance_rate', 'shipping_performance', 'average_rating', 'updated_at']


@admin.register(VerifiedSellerStatus)
class VerifiedSellerStatusAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'verification_level', 'verified_at', 'expires_at', 'verified_by']
    list_filter = ['verification_level']


admin.site.register(User, CustomUserAdmin)