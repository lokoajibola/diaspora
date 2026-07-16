from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    class CountryChoices(models.TextChoices):
        NIGERIA = 'NG', 'Nigeria'
        GHANA = 'GH', 'Ghana'

    class BusinessTypeChoices(models.TextChoices):
        SOLE_PROPRIETORSHIP = 'sole_proprietorship', 'Sole Proprietorship'
        LLC = 'llc', 'Limited Liability Company'
        PARTNERSHIP = 'partnership', 'Partnership'
        CORPORATION = 'corporation', 'Corporation'
        NONPROFIT = 'nonprofit', 'Non-Profit Organization'
        OTHER = 'other', 'Other'

    class IDTypeChoices(models.TextChoices):
        PASSPORT = 'passport', 'International Passport'
        DRIVERS_LICENSE = 'drivers_license', "Driver's License"
        VOTERS_CARD = 'voters_card', "Voter's Card"
        NATIONAL_ID = 'national_id', 'National ID Card'

    class KYCStageChoices(models.TextChoices):
        REGISTRATION = 'registration', 'Registration'
        BUSINESS_INFO = 'business_info', 'Business Information'
        IDENTITY = 'identity', 'Identity Verification'
        CONTACT = 'contact', 'Contact Verification'
        ADDRESS = 'address', 'Address Verification'
        BANKING = 'banking', 'Banking Details'
        GUARANTOR = 'guarantor', 'Guarantor Information'
        COMPLIANCE = 'compliance', 'Product Compliance'
        DOCUMENTS = 'documents', 'Document Upload'
        INTERNAL_CHECK = 'internal_check', 'Internal Checks (Admin)'
        QUALITY_ASSURANCE = 'quality_assurance', 'Quality Assurance (Admin)'
        VERIFIED_SELLER = 'verified_seller', 'Verified Seller'
        APPROVED = 'approved', 'Fully Approved'
        REJECTED = 'rejected', 'Rejected'

    username = None  # Remove username field
    phone_number = models.CharField(max_length=15, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # --- Existing KYC Fields ---
    shop_name = models.CharField(max_length=255, blank=True, null=True)
    shop_address = models.TextField(blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_name = models.CharField(max_length=150, blank=True, null=True)
    bank_account_number = models.CharField(max_length=30, blank=True, null=True)
    id_document = models.ImageField(upload_to='kyc/documents/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # Admin flips this switch
    kyc_rejection_reason = models.TextField(blank=True, null=True)

    # --- P0: Business Information ---
    business_registration_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='CAC/Business Registration Number')
    business_type = models.CharField(max_length=30, choices=BusinessTypeChoices.choices, blank=True, null=True, verbose_name='Business Type')
    business_start_date = models.DateField(blank=True, null=True, verbose_name='Date Business Started')
    business_description = models.TextField(blank=True, null=True, verbose_name='Business Description')
    business_logo = models.ImageField(upload_to='kyc/logos/', blank=True, null=True, verbose_name='Business Logo')
    tin = models.CharField(max_length=20, blank=True, null=True, verbose_name='Tax Identification Number (TIN)')

    # --- P0: Identity Verification ---
    date_of_birth = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=50, blank=True, null=True)
    nin = models.CharField(max_length=11, blank=True, null=True, unique=True, verbose_name='National Identification Number (NIN)')
    bvn = models.CharField(max_length=10, blank=True, null=True, unique=True, verbose_name='Bank Verification Number (BVN)')
    id_document_type = models.CharField(max_length=30, choices=IDTypeChoices.choices, blank=True, null=True, verbose_name='Government ID Type')
    liveness_selfie = models.ImageField(upload_to='kyc/selfies/', blank=True, null=True, verbose_name='Liveness/Selfie Verification')
    passport_photo = models.ImageField(upload_to='kyc/passports/', blank=True, null=True, verbose_name='Passport Photograph')

    # --- P1: Contact Information ---
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)

    # --- P1: Address Verification ---
    home_address = models.TextField(blank=True, null=True)
    utility_bill = models.FileField(upload_to='kyc/utilities/', blank=True, null=True, verbose_name='Utility Bill')

    # --- P1: KYC Stage Tracking ---
    kyc_stage = models.CharField(
        max_length=30,
        choices=KYCStageChoices.choices,
        default=KYCStageChoices.REGISTRATION,
        verbose_name='KYC Stage'
    )
    kyc_submitted_at = models.DateTimeField(blank=True, null=True)
    kyc_approved_at = models.DateTimeField(blank=True, null=True)
    otp_phone_verified = models.BooleanField(default=False, verbose_name='Phone OTP Verified')
    otp_email_verified = models.BooleanField(default=False, verbose_name='Email OTP Verified')

    # --- Role & Country ---
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('logistics', 'Logistics'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    country = models.CharField(max_length=2, choices=CountryChoices.choices, default=CountryChoices.NIGERIA)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.phone_number} ({self.role})"

    @property
    def kyc_progress_percentage(self):
        """Calculate KYC completion percentage based on completed stages"""
        stages = [
            self.kyc_stage in ['business_info', 'identity', 'contact', 'address',
                               'banking', 'guarantor', 'compliance', 'documents',
                               'internal_check', 'quality_assurance', 'verified_seller', 'approved'],
            self.kyc_stage in ['identity', 'contact', 'address', 'banking', 'guarantor',
                               'compliance', 'documents', 'internal_check', 'quality_assurance',
                               'verified_seller', 'approved'],
            self.kyc_stage in ['contact', 'address', 'banking', 'guarantor', 'compliance',
                               'documents', 'internal_check', 'quality_assurance', 'verified_seller', 'approved'],
            self.kyc_stage in ['address', 'banking', 'guarantor', 'compliance', 'documents',
                               'internal_check', 'quality_assurance', 'verified_seller', 'approved'],
            self.kyc_stage in ['banking', 'guarantor', 'compliance', 'documents',
                               'internal_check', 'quality_assurance', 'verified_seller', 'approved'],
            bool(self.bank_name and self.bank_account_name and self.bank_account_number),
        ]
        completed = sum(stages)
        total = 6
        return int((completed / total) * 100)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)  # Click to go to order
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# =====================
# NEW MODELS FOR P0-P2
# =====================

class Guarantor(models.Model):
    """Guarantor information for vendor verification"""
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guarantors')
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    occupation = models.CharField(max_length=100)
    relationship = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.vendor.phone_number}"


class ProductCompliance(models.Model):
    """NAFDAC/SON compliance tracking for vendor products"""
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compliance_records')
    nafdac_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='NAFDAC Registration Number')
    nafdac_document = models.FileField(upload_to='kyc/compliance/nafdac/', blank=True, null=True, verbose_name='NAFDAC Certificate')
    son_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='SON Registration Number')
    son_document = models.FileField(upload_to='kyc/compliance/son/', blank=True, null=True, verbose_name='SON Certificate')
    has_labels = models.BooleanField(default=False, verbose_name='Product Labels Compliant')
    ingredients_list = models.TextField(blank=True, null=True, verbose_name='Ingredients List')
    batch_tracking = models.BooleanField(default=False, verbose_name='Batch Number Tracking')
    expiry_date_policy = models.TextField(blank=True, null=True, verbose_name='Expiry Date Management Policy')
    is_verified = models.BooleanField(default=False, verbose_name='Compliance Verified by Admin')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_verified')
    verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Compliance - {self.vendor.phone_number}"


class KYCInternalCheck(models.Model):
    """Admin internal verification checks for vendor KYC"""
    class CheckStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PASSED = 'passed', 'Passed'
        FAILED = 'failed', 'Failed'
        NOT_APPLICABLE = 'na', 'Not Applicable'

    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='internal_checks')
    nin_verified = models.CharField(max_length=10, choices=CheckStatus.choices, default=CheckStatus.PENDING, verbose_name='NIN Verification')
    bvn_verified = models.CharField(max_length=10, choices=CheckStatus.choices, default=CheckStatus.PENDING, verbose_name='BVN Verification')
    bank_matched = models.CharField(max_length=10, choices=CheckStatus.choices, default=CheckStatus.PENDING, verbose_name='Bank Account Match')
    cac_verified = models.CharField(max_length=10, choices=CheckStatus.choices, default=CheckStatus.PENDING, verbose_name='CAC Verification')
    nafdac_verified = models.CharField(max_length=10, choices=CheckStatus.choices, default=CheckStatus.PENDING, verbose_name='NAFDAC Verification')
    otp_verified = models.CharField(max_length=10, choices=CheckStatus.choices, default=CheckStatus.PENDING, verbose_name='OTP Verification')
    duplicate_checked = models.CharField(max_length=10, choices=CheckStatus.choices, default=CheckStatus.PENDING, verbose_name='Duplicate Check')
    fraud_checked = models.CharField(max_length=10, choices=CheckStatus.choices, default=CheckStatus.PENDING, verbose_name='Fraud Check')
    overall_status = models.CharField(max_length=10, choices=CheckStatus.choices, default=CheckStatus.PENDING, verbose_name='Overall Status')
    notes = models.TextField(blank=True, null=True, verbose_name='Internal Notes')
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kyc_checks_performed')
    checked_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Internal Check - {self.vendor.phone_number} ({self.overall_status})"


class ShopPhoto(models.Model):
    """Multiple shop/warehouse photos for vendor verification"""
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_photos')
    image = models.ImageField(upload_to='kyc/shop_photos/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Shop Photo - {self.vendor.phone_number}"


class QualityAssurance(models.Model):
    """Quality assurance review records for vendor verification"""
    class QAStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        PASSED = 'passed', 'Passed'
        FAILED = 'failed', 'Failed - Needs Corrections'

    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quality_checks')
    shop_photos_ok = models.BooleanField(default=False, verbose_name='Shop/Warehouse Photos OK')
    packaging_photos_ok = models.BooleanField(default=False, verbose_name='Packaging Photos OK')
    inventory_photos_ok = models.BooleanField(default=False, verbose_name='Inventory Photos OK')
    supplier_invoices_ok = models.BooleanField(default=False, verbose_name='Supplier Invoices OK')
    authenticity_proof_ok = models.BooleanField(default=False, verbose_name='Authenticity Proof OK')
    qa_notes = models.TextField(blank=True, null=True, verbose_name='QA Inspector Notes')
    status = models.CharField(max_length=10, choices=QAStatus.choices, default=QAStatus.PENDING)
    qa_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='qa_reviews')
    qa_date = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QA - {self.vendor.phone_number} ({self.status})"


class VendorPerformance(models.Model):
    """Performance metrics tracking for vendors"""
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_metrics')
    total_orders = models.PositiveIntegerField(default=0)
    accepted_orders = models.PositiveIntegerField(default=0)
    shipped_on_time = models.PositiveIntegerField(default=0)
    total_shipped = models.PositiveIntegerField(default=0)
    returned_orders = models.PositiveIntegerField(default=0)
    delivered_orders = models.PositiveIntegerField(default=0)
    complaints = models.PositiveIntegerField(default=0)
    total_ratings = models.PositiveIntegerField(default=0)
    sum_ratings = models.PositiveIntegerField(default=0)
    refunded_orders = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Vendor Performance Metrics'

    @property
    def acceptance_rate(self):
        if self.total_orders == 0:
            return 0
        return round((self.accepted_orders / self.total_orders) * 100, 1)

    @property
    def shipping_performance(self):
        if self.total_shipped == 0:
            return 0
        return round((self.shipped_on_time / self.total_shipped) * 100, 1)

    @property
    def return_rate(self):
        if self.delivered_orders == 0:
            return 0
        return round((self.returned_orders / self.delivered_orders) * 100, 1)

    @property
    def complaint_rate(self):
        if self.total_orders == 0:
            return 0
        return round((self.complaints / self.total_orders) * 100, 1)

    @property
    def average_rating(self):
        if self.total_ratings == 0:
            return 0
        return round(self.sum_ratings / self.total_ratings, 1)

    @property
    def refund_rate(self):
        if self.total_orders == 0:
            return 0
        return round((self.refunded_orders / self.total_orders) * 100, 1)

    def __str__(self):
        return f"Performance - {self.vendor.phone_number}"


class VerifiedSellerStatus(models.Model):
    """Verified seller badge management"""
    class VerificationLevel(models.TextChoices):
        BRONZE = 'bronze', 'Bronze'
        SILVER = 'silver', 'Silver'
        GOLD = 'gold', 'Gold'
        PLATINUM = 'platinum', 'Platinum'

    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verified_seller_status')
    verification_level = models.CharField(max_length=10, choices=VerificationLevel.choices, default=VerificationLevel.BRONZE)
    inspection_done = models.BooleanField(default=False, verbose_name='Physical Inspection Completed')
    video_interview_done = models.BooleanField(default=False, verbose_name='Video Interview Completed')
    supplier_references_ok = models.BooleanField(default=False, verbose_name='Supplier References Verified')
    quality_audit_ok = models.BooleanField(default=False, verbose_name='Quality Audit Passed')
    badge_displayed = models.BooleanField(default=False, verbose_name='Badge Displayed on Products')
    verified_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='seller_verifications')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Verified Seller Statuses'

    def __str__(self):
        return f"{self.vendor.phone_number} - {self.verification_level}"


class OTPVerification(models.Model):
    """OTP code storage for phone and email verification"""
    class OTPTypeChoices(models.TextChoices):
        PHONE = 'phone', 'Phone'
        EMAIL = 'email', 'Email'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=OTPTypeChoices.choices)
    is_verified = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_valid(self):
        """Check if OTP is still valid (not expired, not used)"""
        from django.utils import timezone
        return (
            not self.is_verified and
            not self.is_expired and
            self.expires_at > timezone.now() and
            self.attempts < 5
        )

    def __str__(self):
        return f"{self.user.phone_number} - {self.otp_type} - {'✓' if self.is_verified else '✗'}"
