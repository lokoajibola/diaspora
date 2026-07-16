from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomerRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from orders.models import Order
from django.db.models import Sum, F
from orders.models import OrderItem, PayoutRequest
from products.models import Product
from .models import User, Notification, Guarantor, ProductCompliance, KYCInternalCheck, ShopPhoto, QualityAssurance, VerifiedSellerStatus, OTPVerification
from .otp_utils import create_and_send_otp, verify_otp
from django.utils import timezone
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from orders.utils import ensure_tracking_number, credit_vendors_for_paid_order, reduce_stock_for_paid_order


@staff_member_required
def approve_payout(request, payout_id):
    if request.method == 'POST':
        payout = get_object_or_404(PayoutRequest, id=payout_id)
        transfer_reference = request.POST.get('transfer_reference', '').strip()
        
        if not payout.is_paid:
            with transaction.atomic():
                vendor = payout.vendor
                if not vendor.bank_name or not vendor.bank_account_name or not vendor.bank_account_number:
                    messages.error(request, "Vendor bank details are missing. Ask vendor to complete KYC bank details first.")
                    return redirect('admin_dashboard')

                if not transfer_reference:
                    messages.error(request, "Transfer reference is required to confirm payout.")
                    return redirect('admin_dashboard')

                if vendor.balance >= payout.amount:
                    vendor.balance -= payout.amount
                    vendor.save()
                    
                    payout.is_paid = True
                    payout.transfer_reference = transfer_reference
                    payout.paid_at = timezone.now()
                    payout.processed_by = request.user
                    payout.save()
                    
                    messages.success(request, f"Payout of {payout.amount} for {vendor.shop_name} marked as transferred.")
                else:
                    messages.error(request, "Vendor balance is insufficient for this payout amount.")
            
                Notification.objects.create(
                    user=vendor,
                    message=f"Your payout request of {payout.amount} has been transferred to your bank account.",
                    link="#"
                )
        
        else:
            messages.info(request, "This payout has already been processed.")
    
    return redirect('admin_dashboard')


@staff_member_required
def admin_dashboard(request):
    total_revenue = Order.objects.filter(status__in=['paid', 'shipped', 'delivered']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_vendors = User.objects.filter(role='vendor').count()
    total_customers = User.objects.filter(role='customer').count()
    total_logistics = User.objects.filter(role='logistics').count()
    
    query = request.GET.get('q', '')
    all_orders = Order.objects.all().select_related('customer')
    
    if query:
        all_orders = all_orders.filter(
            Q(id__icontains=query) | 
            Q(receiver_name__icontains=query) | 
            Q(delivery_address__icontains=query) |
            Q(customer__phone_number__icontains=query)
        )

    thirty_days_ago = timezone.now() - timedelta(days=30)
    revenue_data = (
        Order.objects.filter(status='paid', created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(daily_revenue=Sum('total_amount'))
        .order_by('date')
    )

    chart_labels = [data['date'].strftime('%b %d') for data in revenue_data]
    chart_values = [float(data['daily_revenue']) for data in revenue_data]

    payout_requests = PayoutRequest.objects.filter(is_paid=False).select_related('vendor').order_by('-created_at')
    recent_transfers = PayoutRequest.objects.filter(is_paid=True).select_related('vendor', 'processed_by').order_by('-paid_at')[:10]

    pending_payout_total = User.objects.filter(role='vendor').aggregate(Sum('balance'))['balance__sum'] or 0
    transferred_total = PayoutRequest.objects.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0

    managed_users = User.objects.filter(is_superuser=False).order_by('-date_joined')[:20]
    
    # Updated: Show vendors pending internal KYC checks (not just basic is_verified)
    pending_kyc_vendors = User.objects.filter(
        role='vendor',
        is_verified=False
    ).filter(
        Q(kyc_rejection_reason__isnull=True) | Q(kyc_rejection_reason='')
    ).order_by('-date_joined')[:10]
    
    delivery_queue = Order.objects.filter(status__in=['paid', 'shipped']).order_by('-created_at')[:20]

    context = {
        'revenue': total_revenue,
        'order_count': total_orders,
        'vendor_count': total_vendors,
        'customer_count': total_customers,
        'logistics_count': total_logistics,
        'orders': all_orders,
        'query': query,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'payout_requests': payout_requests,
        'recent_transfers': recent_transfers,
        'pending_payout_total': pending_payout_total,
        'transferred_total': transferred_total,
        'managed_users': managed_users,
        'pending_kyc_vendors': pending_kyc_vendors,
        'pending_kyc_count': pending_kyc_vendors.count(),
        'delivery_queue': delivery_queue,
    }
    return render(request, 'admin_custom/dashboard.html', context)


@staff_member_required
def admin_approve_vendor_kyc(request, user_id):
    if request.method == 'POST':
        vendor = get_object_or_404(User, id=user_id, role='vendor')
        vendor.is_verified = True
        vendor.kyc_rejection_reason = None
        vendor.kyc_stage = User.KYCStageChoices.APPROVED
        vendor.kyc_approved_at = timezone.now()
        vendor.save(update_fields=['is_verified', 'kyc_rejection_reason', 'kyc_stage', 'kyc_approved_at'])

        Notification.objects.create(
            user=vendor,
            message="Your KYC has been approved. Your vendor account is now verified.",
            link="#"
        )
        messages.success(request, f"Vendor {vendor.phone_number} KYC approved.")

    return redirect('admin_dashboard')


@staff_member_required
def admin_reject_vendor_kyc(request, user_id):
    if request.method == 'POST':
        vendor = get_object_or_404(User, id=user_id, role='vendor')
        rejection_reason = request.POST.get('rejection_reason', '').strip()

        if not rejection_reason:
            messages.error(request, "Rejection reason is required.")
            return redirect('admin_dashboard')

        vendor.is_verified = False
        vendor.kyc_rejection_reason = rejection_reason
        vendor.kyc_stage = User.KYCStageChoices.REJECTED
        vendor.save(update_fields=['is_verified', 'kyc_rejection_reason', 'kyc_stage'])

        Notification.objects.create(
            user=vendor,
            message=f"Your KYC was rejected. Reason: {rejection_reason}",
            link="#"
        )
        messages.info(request, f"Vendor {vendor.phone_number} KYC rejected.")

    return redirect('admin_dashboard')


@staff_member_required
def admin_update_user(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        is_verified = request.POST.get('is_verified') == 'on'

        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if role in valid_roles:
            target_user.role = role

        target_user.is_active = is_active
        target_user.is_verified = is_verified
        target_user.save()
        messages.success(request, f"User {target_user.phone_number} updated.")

    return redirect('admin_dashboard')


@staff_member_required
def admin_update_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        # Validation to ensure the status is one of our choices
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status in valid_statuses:
            order.status = new_status

            if new_status == 'paid':
                ensure_tracking_number(order)

            order.save()

            if new_status == 'paid':
                credit_vendors_for_paid_order(order)
                reduce_stock_for_paid_order(order)
                order.save(update_fields=['vendor_credit_processed', 'stock_deducted'])

            messages.success(request, f"Order #{order.id} updated to {order.get_status_display()}.")
        else:
            messages.error(request, "Invalid status selected.")
            
    return redirect('admin_dashboard')


@login_required
def vendor_notifications(request):
    notifications = request.user.notifications.all()
    # Mark all as read when they visit this page
    notifications.update(is_read=True)
    return render(request, 'users/notifications.html', {'notifications': notifications})


@login_required
def vendor_dashboard(request):
    if request.user.role != 'vendor':
        return redirect('home')

    my_products = Product.objects.filter(vendor=request.user)

    vendor_sales = OrderItem.objects.filter(
        product__vendor=request.user,
        order__status__in=['paid', 'shipped', 'delivered']
    ).select_related('order', 'product')

    vendor_orders = (
        Order.objects
        .filter(items__product__vendor=request.user, status__in=['paid', 'shipped', 'delivered'])
        .select_related('customer')
        .distinct()
        .order_by('-created_at')
    )

    total_revenue = vendor_sales.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or 0

    active_orders_count = vendor_orders.filter(status__in=['paid', 'shipped']).count()
    low_stock_products = my_products.filter(stock__lte=F('low_stock_threshold')).order_by('stock')
    
    # Enhanced KYC status check - check new fields
    has_kyc_details = all([
        request.user.shop_name,
        request.user.shop_address,
        request.user.bank_name,
        request.user.bank_account_name,
        request.user.bank_account_number,
        request.user.id_document,
    ])

    context = {
        'products': my_products,
        'sales': vendor_sales,
        'sold_items': vendor_sales.order_by('-order__created_at'),
        'total_revenue': total_revenue,
        'orders': vendor_orders,
        'active_orders_count': active_orders_count,
        'total_products_count': my_products.count(),
        'paid_orders_count': vendor_orders.filter(status='paid').count(),
        'total_stock_quantity': my_products.aggregate(total=Sum('stock'))['total'] or 0,
        'low_stock_products': low_stock_products,
        'has_kyc_details': has_kyc_details,
    }
    return render(request, 'users/vendor_dashboard.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        return redirect('home')
    return render(request, 'registration/edit_profile.html')


@login_required
def logistics_dashboard(request):
    if request.user.role != 'logistics' and not request.user.is_staff:
        return redirect('home')
    
    # Show orders that need attention
    pending_shipments = Order.objects.filter(status__in=['paid', 'shipped']).order_by('-created_at')
    return render(request, 'users/logistics_dashboard.html', {'orders': pending_shipments})


@login_required
def update_order_status(request, order_id, new_status):
    if request.user.role == 'logistics' or request.user.is_staff:
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()
    return redirect('logistics_dashboard')


@login_required
def request_payout(request):
    if request.user.role != 'vendor':
        return redirect('home')

    if not request.user.bank_name or not request.user.bank_account_name or not request.user.bank_account_number:
        messages.error(request, "Please complete your bank details in KYC before requesting payout.")
        return redirect('vendor_kyc')

    if request.user.balance > 0:
        PayoutRequest.objects.create(
            vendor=request.user,
            amount=request.user.balance
        )
        # Optionally reset balance to 0 immediately or wait until Admin approves
        messages.success(request, "Payout request submitted! Admin will review it shortly.")
    else:
        messages.error(request, "Your balance is 0.00.")

    return redirect('vendor_dashboard')


# =============================================
# MULTI-STEP KYC VIEWS (P0 Implementation)
# =============================================

@login_required
def vendor_kyc_dashboard(request):
    """KYC Status Dashboard - Shows overall progress and current stage"""
    if request.user.role != 'vendor':
        return redirect('home')
    
    user = request.user
    has_pending_rejection = bool(user.kyc_rejection_reason)
    
    context = {
        'kyc_stage': user.kyc_stage,
        'kyc_progress': user.kyc_progress_percentage,
        'has_pending_rejection': has_pending_rejection,
        'rejection_reason': user.kyc_rejection_reason,
        'otp_phone_verified': user.otp_phone_verified,
        'otp_email_verified': user.otp_email_verified,
    }
    return render(request, 'users/kyc_dashboard.html', context)


@login_required
def vendor_kyc_step(request, step):
    """Handle multi-step KYC forms"""
    if request.user.role != 'vendor':
        return redirect('home')
    
    user = request.user
    valid_steps = ['business', 'identity', 'contact', 'address', 'banking']
    
    if step not in valid_steps:
        messages.error(request, "Invalid KYC step.")
        return redirect('vendor_kyc_dashboard')
    
    if request.method == 'POST':
        return _process_kyc_step(request, user, step)
    
    # GET - render the appropriate form
    context = _get_kyc_step_context(user, step)
    return render(request, f'users/kyc_step_{step}.html', context)


def _process_kyc_step(request, user, step):
    """Process KYC step form submission"""
    
    if step == 'business':
        user.business_registration_number = request.POST.get('business_registration_number', '').strip()
        user.business_type = request.POST.get('business_type', '').strip()
        business_start_date_str = request.POST.get('business_start_date', '').strip()
        if business_start_date_str:
            from datetime import datetime
            try:
                user.business_start_date = datetime.strptime(business_start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        user.business_description = request.POST.get('business_description', '').strip()
        user.tin = request.POST.get('tin', '').strip()
        user.shop_name = request.POST.get('shop_name', '').strip()
        
        if 'business_logo' in request.FILES:
            user.business_logo = request.FILES['business_logo']
        
        # Advance stage
        user.kyc_stage = User.KYCStageChoices.IDENTITY
        
    elif step == 'identity':
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        dob_str = request.POST.get('date_of_birth', '').strip()
        if dob_str:
            from datetime import datetime
            try:
                user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        user.nationality = request.POST.get('nationality', '').strip()
        user.nin = request.POST.get('nin', '').strip()
        user.bvn = request.POST.get('bvn', '').strip()
        user.id_document_type = request.POST.get('id_document_type', '').strip()
        
        if 'id_document' in request.FILES:
            user.id_document = request.FILES['id_document']
        if 'liveness_selfie' in request.FILES:
            user.liveness_selfie = request.FILES['liveness_selfie']
        if 'passport_photo' in request.FILES:
            user.passport_photo = request.FILES['passport_photo']
        
        user.kyc_stage = User.KYCStageChoices.CONTACT
        
    elif step == 'contact':
        user.email = request.POST.get('email', '').strip()
        user.whatsapp_number = request.POST.get('whatsapp_number', '').strip()
        user.emergency_contact_name = request.POST.get('emergency_contact_name', '').strip()
        user.emergency_contact_phone = request.POST.get('emergency_contact_phone', '').strip()
        
        user.kyc_stage = User.KYCStageChoices.ADDRESS
        
    elif step == 'address':
        user.home_address = request.POST.get('home_address', '').strip()
        user.shop_address = request.POST.get('shop_address', '').strip()
        
        if 'utility_bill' in request.FILES:
            user.utility_bill = request.FILES['utility_bill']
        
        # Handle shop photos
        if 'shop_photos' in request.FILES:
            files = request.FILES.getlist('shop_photos')
            for f in files:
                ShopPhoto.objects.create(vendor=user, image=f)
        
        user.kyc_stage = User.KYCStageChoices.BANKING
        
    elif step == 'banking':
        user.bank_name = request.POST.get('bank_name', '').strip()
        user.bank_account_name = request.POST.get('bank_account_name', '').strip()
        user.bank_account_number = request.POST.get('bank_account_number', '').strip()
        
        # Guarantor info (optional but tracked)
        guarantor_name = request.POST.get('guarantor_name', '').strip()
        if guarantor_name:
            Guarantor.objects.create(
                vendor=user,
                full_name=guarantor_name,
                phone_number=request.POST.get('guarantor_phone', '').strip(),
                address=request.POST.get('guarantor_address', '').strip(),
                occupation=request.POST.get('guarantor_occupation', '').strip(),
                relationship=request.POST.get('guarantor_relationship', '').strip(),
            )
        
        # Compliance info
        nafdac_number = request.POST.get('nafdac_number', '').strip()
        if nafdac_number:
            compliance = ProductCompliance.objects.create(
                vendor=user,
                nafdac_number=nafdac_number,
                son_number=request.POST.get('son_number', '').strip(),
                has_labels=request.POST.get('has_labels') == 'on',
                ingredients_list=request.POST.get('ingredients_list', '').strip(),
                batch_tracking=request.POST.get('batch_tracking') == 'on',
                expiry_date_policy=request.POST.get('expiry_date_policy', '').strip(),
            )
            if 'nafdac_document' in request.FILES:
                compliance.nafdac_document = request.FILES['nafdac_document']
            if 'son_document' in request.FILES:
                compliance.son_document = request.FILES['son_document']
            compliance.save()
        
        # Mark KYC as submitted and advance to internal check
        user.kyc_stage = User.KYCStageChoices.INTERNAL_CHECK
        user.kyc_submitted_at = timezone.now()
        
        # Create internal check record for admin
        KYCInternalCheck.objects.get_or_create(vendor=user)
        
        messages.success(request, "KYC submitted successfully! Admin will review your information.")
    
    user.save()
    messages.success(request, f"{step.title()} information saved successfully!")
    
    if step == 'banking':
        return redirect('vendor_kyc_dashboard')
    return redirect('vendor_kyc_step', step=_get_next_step(step))


def _get_next_step(current_step):
    """Get the next KYC step"""
    steps = ['business', 'identity', 'contact', 'address', 'banking']
    try:
        idx = steps.index(current_step)
        if idx < len(steps) - 1:
            return steps[idx + 1]
    except ValueError:
        pass
    return 'business'


def _get_kyc_step_context(user, step):
    """Get context data for KYC step templates"""
    context = {
        'user': user,
        'kyc_stage': user.kyc_stage,
    }
    
    if step == 'banking':
        context['guarantors'] = user.guarantors.all()
        context['compliance'] = user.compliance_records.first()
    
    return context


# =============================================
# ADMIN KYC REVIEW VIEWS (P0 Implementation)
# =============================================

@staff_member_required
def admin_kyc_review_list(request):
    """Admin panel to view all pending KYC applications"""
    status_filter = request.GET.get('status', 'pending')
    
    if status_filter == 'pending':
        vendors = User.objects.filter(
            role='vendor',
            kyc_stage=User.KYCStageChoices.INTERNAL_CHECK
        ).order_by('-kyc_submitted_at')
    elif status_filter == 'approved':
        vendors = User.objects.filter(
            role='vendor',
            kyc_stage=User.KYCStageChoices.APPROVED
        ).order_by('-kyc_approved_at')
    elif status_filter == 'rejected':
        vendors = User.objects.filter(
            role='vendor',
            kyc_stage=User.KYCStageChoices.REJECTED
        ).order_by('-date_joined')
    else:
        vendors = User.objects.filter(role='vendor').order_by('-date_joined')
    
    context = {
        'vendors': vendors,
        'current_filter': status_filter,
        'pending_count': User.objects.filter(
            role='vendor',
            kyc_stage=User.KYCStageChoices.INTERNAL_CHECK
        ).count(),
    }
    return render(request, 'admin_custom/kyc_review_list.html', context)


@staff_member_required
def admin_kyc_review_detail(request, user_id):
    """Admin panel to review a single vendor's full KYC submission"""
    vendor = get_object_or_404(User, id=user_id, role='vendor')
    internal_check = KYCInternalCheck.objects.filter(vendor=vendor).first()
    guarantors = vendor.guarantors.all()
    compliance = vendor.compliance_records.first()
    shop_photos = vendor.shop_photos.all()
    
    context = {
        'vendor': vendor,
        'internal_check': internal_check,
        'guarantors': guarantors,
        'compliance': compliance,
        'shop_photos': shop_photos,
    }
    return render(request, 'admin_custom/kyc_review_detail.html', context)


@staff_member_required
def admin_kyc_perform_checks(request, user_id):
    """Admin performs internal KYC checks - renders form on GET, processes on POST"""
    vendor = get_object_or_404(User, id=user_id, role='vendor')
    
    if request.method == 'POST':
        check, created = KYCInternalCheck.objects.get_or_create(vendor=vendor)
        
        check.nin_verified = request.POST.get('nin_verified', 'pending')
        check.bvn_verified = request.POST.get('bvn_verified', 'pending')
        check.bank_matched = request.POST.get('bank_matched', 'pending')
        check.cac_verified = request.POST.get('cac_verified', 'pending')
        check.nafdac_verified = request.POST.get('nafdac_verified', 'pending')
        check.otp_verified = request.POST.get('otp_verified', 'pending')
        check.duplicate_checked = request.POST.get('duplicate_checked', 'pending')
        check.fraud_checked = request.POST.get('fraud_checked', 'pending')
        check.notes = request.POST.get('notes', '').strip()
        check.checked_by = request.user
        
        # Determine overall status
        statuses = [
            check.nin_verified, check.bvn_verified, check.bank_matched,
            check.cac_verified, check.nafdac_verified, check.otp_verified,
            check.duplicate_checked, check.fraud_checked
        ]
        if 'failed' in statuses:
            check.overall_status = KYCInternalCheck.CheckStatus.FAILED
        elif all(s == KYCInternalCheck.CheckStatus.PASSED or s == KYCInternalCheck.CheckStatus.NOT_APPLICABLE for s in statuses):
            check.overall_status = KYCInternalCheck.CheckStatus.PASSED
        else:
            check.overall_status = KYCInternalCheck.CheckStatus.PENDING
        
        check.save()
        
        # Update vendor KYC stage based on results
        if check.overall_status == KYCInternalCheck.CheckStatus.PASSED:
            vendor.kyc_stage = User.KYCStageChoices.QUALITY_ASSURANCE
            vendor.save(update_fields=['kyc_stage'])
            messages.success(request, f"Internal checks passed for {vendor.phone_number}. Moving to QA stage.")
        elif check.overall_status == KYCInternalCheck.CheckStatus.FAILED:
            vendor.kyc_stage = User.KYCStageChoices.REJECTED
            vendor.kyc_rejection_reason = check.notes or 'Internal checks failed'
            vendor.save(update_fields=['kyc_stage', 'kyc_rejection_reason'])
            messages.warning(request, f"Internal checks failed for {vendor.phone_number}.")
        else:
            messages.info(request, f"Checks saved as pending for {vendor.phone_number}.")
        
        return redirect('admin_kyc_review_detail', user_id=user_id)
    
    # GET request - render the internal checks form
    internal_check = KYCInternalCheck.objects.filter(vendor=vendor).first()
    context = {
        'vendor': vendor,
        'internal_check': internal_check,
    }
    return render(request, 'admin_custom/kyc_internal_checks.html', context)


@staff_member_required
def admin_qa_review(request, user_id):
    """Admin quality assurance review"""
    vendor = get_object_or_404(User, id=user_id, role='vendor')
    
    if request.method == 'POST':
        qa, created = QualityAssurance.objects.get_or_create(vendor=vendor)
        
        qa.shop_photos_ok = request.POST.get('shop_photos_ok') == 'on'
        qa.packaging_photos_ok = request.POST.get('packaging_photos_ok') == 'on'
        qa.inventory_photos_ok = request.POST.get('inventory_photos_ok') == 'on'
        qa.supplier_invoices_ok = request.POST.get('supplier_invoices_ok') == 'on'
        qa.authenticity_proof_ok = request.POST.get('authenticity_proof_ok') == 'on'
        qa.qa_notes = request.POST.get('qa_notes', '').strip()
        qa.qa_officer = request.user
        
        action = request.POST.get('action', 'save')
        if action == 'pass':
            qa.status = QualityAssurance.QAStatus.PASSED
            vendor.kyc_stage = User.KYCStageChoices.VERIFIED_SELLER
            vendor.is_verified = True
            vendor.save(update_fields=['kyc_stage', 'is_verified'])
            messages.success(request, f"QA passed for {vendor.phone_number}. Vendor is now verified!")
        elif action == 'fail':
            qa.status = QualityAssurance.QAStatus.FAILED
            vendor.kyc_stage = User.KYCStageChoices.REJECTED
            vendor.kyc_rejection_reason = qa.qa_notes or 'QA review failed'
            vendor.save(update_fields=['kyc_stage', 'kyc_rejection_reason'])
            messages.warning(request, f"QA failed for {vendor.phone_number}.")
        
        qa.save()
        return redirect('admin_kyc_review_detail', user_id=user_id)
    
    qa = QualityAssurance.objects.filter(vendor=vendor).first()
    shop_photos = vendor.shop_photos.all()
    context = {
        'vendor': vendor,
        'qa': qa,
        'shop_photos': shop_photos,
    }
    return render(request, 'admin_custom/qa_review.html', context)


@staff_member_required
def admin_verified_seller(request, user_id):
    """Admin assigns verified seller badge"""
    vendor = get_object_or_404(User, id=user_id, role='vendor')
    
    if request.method == 'POST':
        vs, created = VerifiedSellerStatus.objects.get_or_create(vendor=vendor)
        
        vs.verification_level = request.POST.get('verification_level', 'bronze')
        vs.inspection_done = request.POST.get('inspection_done') == 'on'
        vs.video_interview_done = request.POST.get('video_interview_done') == 'on'
        vs.supplier_references_ok = request.POST.get('supplier_references_ok') == 'on'
        vs.quality_audit_ok = request.POST.get('quality_audit_ok') == 'on'
        vs.badge_displayed = request.POST.get('badge_displayed') == 'on'
        vs.verified_by = request.user
        vs.verified_at = timezone.now()
        
        # Set expiry (1 year from now)
        vs.expires_at = timezone.now() + timedelta(days=365)
        
        vs.save()
        
        vendor.kyc_stage = User.KYCStageChoices.APPROVED
        vendor.is_verified = True
        vendor.kyc_approved_at = timezone.now()
        vendor.save(update_fields=['kyc_stage', 'is_verified', 'kyc_approved_at'])
        
        Notification.objects.create(
            user=vendor,
            message=f"Congratulations! You've earned the {vs.get_verification_level_display()} Verified Seller badge!",
            link="#"
        )
        
        messages.success(request, f"{vendor.phone_number} is now a verified {vs.get_verification_level_display()} seller!")
        return redirect('admin_kyc_review_detail', user_id=user_id)
    
    vs = VerifiedSellerStatus.objects.filter(vendor=vendor).first()
    context = {
        'vendor': vendor,
        'verified_seller': vs,
    }
    return render(request, 'admin_custom/verified_seller_form.html', context)


# =============================================
# OTP VERIFICATION VIEWS
# =============================================

@login_required
def otp_request(request, otp_type):
    """
    Request a new OTP code
    otp_type: 'phone' or 'email'
    Sends via SMS/WhatsApp for phone, email for email
    """
    if otp_type not in ['phone', 'email']:
        messages.error(request, "Invalid OTP type.")
        return redirect('vendor_kyc_dashboard')
    
    user = request.user
    
    # For email OTP, ensure user has an email
    if otp_type == 'email' and not user.email:
        messages.error(request, "Please set your email address first before requesting email verification.")
        return redirect('vendor_kyc_step', step='contact')
    
    # Determine delivery method for phone
    method = request.GET.get('method', 'sms')
    if method not in ['sms', 'whatsapp']:
        method = 'sms'
    
    success, msg = create_and_send_otp(user, otp_type=otp_type, method=method)
    
    if success:
        messages.success(request, msg or f"OTP sent to your {otp_type}!")
    else:
        messages.error(request, msg or f"Failed to send OTP. Please try again.")
    
    return redirect('otp_verify', otp_type=otp_type)


@login_required
def otp_verify_page(request, otp_type):
    """Display OTP verification page"""
    if otp_type not in ['phone', 'email']:
        messages.error(request, "Invalid OTP type.")
        return redirect('vendor_kyc_dashboard')
    
    user = request.user
    
    # Check if already verified
    if otp_type == 'phone' and user.otp_phone_verified:
        messages.info(request, "Your phone number is already verified.")
        return redirect('vendor_kyc_dashboard')
    if otp_type == 'email' and user.otp_email_verified:
        messages.info(request, "Your email is already verified.")
        return redirect('vendor_kyc_dashboard')
    
    # Check for existing valid OTP
    from datetime import timedelta
    from django.utils import timezone
    expiry_time = timezone.now() - timedelta(minutes=10)
    existing_otp = OTPVerification.objects.filter(
        user=user,
        otp_type=otp_type,
        is_verified=False,
        is_expired=False,
        created_at__gte=expiry_time
    ).first()
    
    context = {
        'otp_type': otp_type,
        'contact_value': user.phone_number if otp_type == 'phone' else user.email,
        'has_pending_otp': existing_otp is not None,
        'otp_sent': request.GET.get('sent', False),
    }
    return render(request, 'users/otp_verify.html', context)


@login_required
def otp_verify_submit(request, otp_type):
    """Verify submitted OTP code"""
    if otp_type not in ['phone', 'email']:
        messages.error(request, "Invalid OTP type.")
        return redirect('vendor_kyc_dashboard')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code or len(otp_code) != 6 or not otp_code.isdigit():
            messages.error(request, "Please enter a valid 6-digit OTP code.")
            return redirect('otp_verify', otp_type=otp_type)
        
        is_valid, msg = verify_otp(request.user, otp_code, otp_type=otp_type)
        
        if is_valid:
            messages.success(request, f"Your {otp_type} has been verified successfully!")
            return redirect('vendor_kyc_dashboard')
        else:
            messages.error(request, msg)
            return redirect('otp_verify', otp_type=otp_type)
    
    return redirect('otp_verify', otp_type=otp_type)


# =============================================
# LEGACY KYC VIEW (Kept for backward compatibility)
# =============================================

@login_required
def vendor_kyc(request):
    """Legacy single-page KYC - redirects to new multi-step flow"""
    if request.user.role != 'vendor':
        return redirect('home')
    
    # Redirect to new KYC dashboard
    return redirect('vendor_kyc_dashboard')


def register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # If user registered as vendor, auto-advance KYC stage
            if user.role == 'vendor':
                user.kyc_stage = User.KYCStageChoices.BUSINESS_INFO
                user.save(update_fields=['kyc_stage'])
            messages.success(request, "Account created! You can now login.")
            return redirect('login')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def role_based_redirect(request):
    user = request.user
    if user.is_staff or user.role == 'admin':
        return redirect('/admin/')
    elif user.role == 'vendor':
        return redirect('vendor_dashboard')
    elif user.role == 'logistics':
        return redirect('logistics_dashboard')
    else:
        return redirect('home')


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.role == 'admin' or user.is_superuser:
            return reverse_lazy('admin_dashboard')
        elif user.role == 'vendor':
            return reverse_lazy('vendor_dashboard')
        elif user.role == 'logistics':
            return reverse_lazy('logistics_dashboard')
        else:
            # Customers go to the home page or order tracking
            return reverse_lazy('home')