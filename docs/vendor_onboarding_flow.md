# ReachAfrica Vendor Onboarding & KYC Process Flow

## Overview
This document defines the refined vendor onboarding process flow, mapping the comprehensive KYC checklist to the current system implementation and identifying all gaps, stages, and implementation requirements.

---

## 1. ONBOARDING STAGES OVERVIEW

```
Registration → Business Info → Identity Verification → Contact Verification
    → Address Verification → Banking → Guarantor → Product Compliance
    → Product Upload → Internal Checks → Quality Assurance → Performance Review
    → Verified Seller Status
```

---

## 2. STAGE-BY-STAGE FLOW

### STAGE 0: Registration (EXISTING - Needs Enhancement)
**Current Status:** ✅ Partially implemented in `users/views.py` (register view) and `users/forms.py`

| Field | Status | Implementation |
|-------|--------|----------------|
| Phone Number | ✅ Done | `phone_number` field in User model |
| Email | ✅ Done | `email` field in User model |
| Password | ✅ Done | Django auth |
| Role Selection | ✅ Done | `role` field (customer/vendor/logistics) |
| Country | ✅ Done | `country` field (NG/GH) |
| First/Last Name | ✅ Done | `first_name`, `last_name` fields |

**Refinement Needed:**
- Add WhatsApp field to registration form
- Add OTP verification step for phone (currently field exists but no verification)
- Add email OTP verification step
- Add referral source tracking

---

### STAGE 1: Business Information (MISSING - Needs Full Implementation)
**Current Status:** ❌ Only `shop_name` exists

| Field | Status | Model Field Needed | Form Field |
|-------|--------|-------------------|------------|
| Business Name | ✅ Partial | `shop_name` exists | Already in KYC form |
| Business Registration (CAC) | ❌ Missing | `business_registration_number` | New field needed |
| Business Type | ❌ Missing | `business_type` (choices: Sole Proprietorship, LLC, Partnership, etc.) | New field needed |
| Date Business Started | ❌ Missing | `business_start_date` | New field needed |
| Business Description | ❌ Missing | `business_description` | New field needed |
| Business Logo | ❌ Missing | `business_logo` (ImageField) | New field needed |
| TIN (Tax ID) | ❌ Missing | `tin` | New field needed |

**Implementation Priority:** HIGH - Required before vendor can list products

---

### STAGE 2: Identity Verification (MISSING - Needs Full Implementation)
**Current Status:** ❌ Only generic `id_document` exists

| Field | Status | Model Field Needed | Notes |
|-------|--------|-------------------|-------|
| Full Name | ✅ Partial | `first_name` + `last_name` | Already exists |
| Date of Birth | ❌ Missing | `date_of_birth` (DateField) | New field needed |
| Nationality | ❌ Missing | `nationality` (CharField) | New field needed |
| NIN (National ID) | ❌ Missing | `nin` (CharField, unique) | New field needed |
| BVN (Bank Verification) | ❌ Missing | `bvn` (CharField, unique) | New field needed |
| Government ID Type | ❌ Missing | `id_document_type` (choices: Passport, Driver's License, Voter's Card, National ID) | New field needed |
| Government ID Upload | ✅ Partial | `id_document` exists | Already in KYC form |
| Selfie/Liveness | ❌ Missing | `liveness_selfie` (ImageField) | New field needed |
| Passport Photograph | ❌ Missing | `passport_photo` (ImageField) | New field needed |

**Implementation Priority:** HIGH - Core KYC requirement

---

### STAGE 3: Contact Verification (PARTIALLY IMPLEMENTED)
**Current Status:** ⚠️ Phone and Email exist but OTP verification not implemented

| Field | Status | Notes |
|-------|--------|-------|
| Phone (OTP) | ⚠️ Partial | Field exists, OTP verification not implemented |
| Email (OTP) | ⚠️ Partial | Field exists, OTP verification not implemented |
| WhatsApp | ❌ Missing | New field needed: `whatsapp_number` |
| Emergency Contact | ❌ Missing | New fields needed: `emergency_contact_name`, `emergency_contact_phone` |

**Implementation Priority:** MEDIUM

---

### STAGE 4: Address Verification (PARTIALLY IMPLEMENTED)
**Current Status:** ⚠️ Only `shop_address` exists

| Field | Status | Model Field Needed |
|-------|--------|-------------------|
| Home Address | ❌ Missing | `home_address` (TextField) |
| Utility Bill Upload | ❌ Missing | `utility_bill` (FileField/ImageField) |
| Business Address | ✅ Partial | `shop_address` exists |
| Shop/Warehouse Photos | ❌ Missing | `shop_photos` (Multiple ImageField or separate model) |

**Implementation Priority:** HIGH - Required for trust and verification

---

### STAGE 5: Banking (PARTIALLY IMPLEMENTED)
**Current Status:** ⚠️ Bank details exist but BVN verification missing

| Field | Status | Notes |
|-------|--------|-------|
| Bank Name | ✅ Done | `bank_name` field exists |
| Account Name | ✅ Done | `bank_account_name` field exists |
| Account Number | ✅ Done | `bank_account_number` field exists |
| BVN Verification | ❌ Missing | `bvn` field needed (shared with Identity stage) |

**Implementation Priority:** HIGH - Required for payouts

---

### STAGE 6: Guarantor (MISSING - Needs Full Implementation)
**Current Status:** ❌ Not implemented

**New Model Needed:** `Guarantor`

| Field | Type | Notes |
|-------|------|-------|
| vendor | ForeignKey(User) | Link to vendor |
| full_name | CharField | Guarantor's full name |
| phone_number | CharField | Guarantor's phone |
| address | TextField | Guarantor's address |
| occupation | CharField | Guarantor's occupation |
| relationship | CharField | Relationship to vendor |
| created_at | DateTimeField | Auto timestamp |

**Implementation Priority:** MEDIUM - Required for high-value vendors

---

### STAGE 7: Product Compliance (MISSING - Needs Full Implementation)
**Current Status:** ❌ Not implemented in vendor onboarding

**New Model Needed:** `ProductCompliance`

| Field | Type | Notes |
|-------|------|-------|
| vendor | ForeignKey(User) | Link to vendor |
| nafdac_number | CharField | NAFDAC registration for food/cosmetics/medicines |
| nafdac_document | FileField | NAFDAC certificate upload |
| son_number | CharField | SON registration where applicable |
| son_document | FileField | SON certificate upload |
| has_labels | BooleanField | Product labels compliance |
| ingredients_list | TextField | Ingredients disclosure |
| batch_tracking | BooleanField | Batch number tracking |
| expiry_date_policy | TextField | Expiry date management policy |
| is_verified | BooleanField | Compliance verified by admin |

**Implementation Priority:** HIGH - Required for regulated products

---

### STAGE 8: Product Upload (EXISTING - Needs Enhancement)
**Current Status:** ⚠️ Basic product model exists in `products/models.py`

**Refinement Needed:**
- Enforce minimum 5 images per product
- Add Brand field (separate model or CharField)
- Add Category as required field with hierarchy
- Add Weight, Dimensions fields
- Add Country of Origin field
- Add Return Policy field
- Add Warranty field
- Add compliance check before product can go live

---

### STAGE 9: Internal Checks (MISSING - Needs Full Implementation)
**Current Status:** ❌ Not implemented

**New Model Needed:** `KYCInternalCheck`

| Check | Description | Status Field |
|-------|-------------|-------------|
| NIN Verification | Verify NIN against NIMC database | `nin_verified` (BooleanField) |
| BVN Verification | Verify BVN against NIBSS | `bvn_verified` (BooleanField) |
| Bank Account Match | Verify bank name matches account | `bank_matched` (BooleanField) |
| CAC Verification | Verify business registration | `cac_verified` (BooleanField) |
| NAFDAC Verification | Verify NAFDAC registration | `nafdac_verified` (BooleanField) |
| OTP Verification | Confirm OTP validation | `otp_verified` (BooleanField) |
| Duplicate Check | Check for duplicate registrations | `duplicate_checked` (BooleanField) |
| Fraud Check | Screen against fraud database | `fraud_checked` (BooleanField) |
| Overall Status | Pass/Fail/Pending | `status` (CharField) |
| Checked By | Admin who performed checks | `checked_by` (ForeignKey) |
| Checked At | Timestamp | `checked_at` (DateTimeField) |

**Implementation Priority:** HIGH - Core admin verification workflow

---

### STAGE 10: Quality Assurance (MISSING - Needs Full Implementation)
**Current Status:** ❌ Not implemented

**New Model Needed:** `QualityAssurance`

| Field | Type | Notes |
|-------|------|-------|
| vendor | ForeignKey(User) | Link to vendor |
| shop_photos_ok | BooleanField | Shop/warehouse photos reviewed |
| packaging_photos_ok | BooleanField | Packaging photos reviewed |
| inventory_photos_ok | BooleanField | Inventory photos reviewed |
| supplier_invoices_ok | BooleanField | Supplier invoices reviewed |
| authenticity_proof_ok | BooleanField | Authenticity proof reviewed |
| qa_notes | TextField | QA inspector notes |
| qa_officer | ForeignKey(User) | Who performed QA |
| qa_date | DateTimeField | When QA was performed |
| status | CharField | Pass/Fail/Pending |

**Implementation Priority:** MEDIUM - Required for Verified Seller badge

---

### STAGE 11: Performance Monitoring (MISSING - Needs Full Implementation)
**Current Status:** ❌ Not implemented

**New Model Needed:** `VendorPerformance`

| Metric | Description | Calculation |
|--------|-------------|-------------|
| Acceptance Rate | % of orders accepted | `accepted_orders / total_orders * 100` |
| Shipping Performance | On-time shipping rate | `shipped_on_time / total_shipped * 100` |
| Return Rate | % of orders returned | `returned_orders / delivered_orders * 100` |
| Complaint Rate | % of orders with complaints | `complaints / total_orders * 100` |
| Average Rating | Customer rating average | `SUM(ratings) / COUNT(ratings)` |
| Refund Rate | % of orders refunded | `refunded_orders / paid_orders * 100` |

**Implementation Priority:** LOW - Ongoing monitoring after onboarding

---

### STAGE 12: Verified Seller Status (MISSING - Needs Full Implementation)
**Current Status:** ⚠️ Basic `is_verified` boolean exists

**Refinement Needed:**

| Component | Description | Status |
|-----------|-------------|--------|
| Physical Inspection | On-site inspection of business | ❌ Missing |
| Video Interview | Interview with vendor | ❌ Missing |
| Supplier References | Contact supplier references | ❌ Missing |
| Quality Audit | Full quality audit | ❌ Missing |
| Verified Badge | Display verified badge on products | ❌ Missing |
| Verification Level | Bronze/Silver/Gold/Platinum | ❌ Missing |
| Verification Expiry | Re-verification schedule | ❌ Missing |

**New Model Needed:** `VerifiedSellerStatus`

| Field | Type |
|-------|------|
| vendor | ForeignKey(User) |
| verification_level | CharField (Bronze/Silver/Gold/Platinum) |
| inspection_done | BooleanField |
| video_interview_done | BooleanField |
| supplier_references_ok | BooleanField |
| quality_audit_ok | BooleanField |
| badge_displayed | BooleanField |
| verified_at | DateTimeField |
| expires_at | DateTimeField |
| verified_by | ForeignKey(User) |

---

## 3. REFINED ONBOARDING PROCESS FLOW

### Flow Diagram (Text)

```
                    ┌─────────────────┐
                    │  Registration   │
                    │  (Phone/Email)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  OTP Verify     │
                    │  Phone + Email  │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  Vendor Application      │
              │  - Business Info         │
              │  - Identity Documents    │
              │  - Contact Details       │
              │  - Address Verification  │
              │  - Banking Details       │
              │  - Guarantor Info        │
              └────────────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  Document Upload         │
              │  - ID Documents          │
              │  - Utility Bill          │
              │  - Shop Photos           │
              │  - Business Registration │
              │  - NAFDAC/SON Certs      │
              └────────────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │  Internal Checks (Admin) │
              │  - NIN Verification      │
              │  - BVN Verification      │
              │  - Bank Account Match    │
              │  - CAC Verification      │
              │  - NAFDAC Verification   │
              │  - Duplicate/Fraud Check │
              └────────────┬─────────────┘
                           │
              ┌────────────┴────────────┐
              │                        │
              ▼                        ▼
     ┌─────────────────┐    ┌─────────────────┐
     │  KYC REJECTED   │    │  KYC APPROVED   │
     │  Notify Vendor  │    │  Stage 1 Passed │
     │  + Reason       │    └────────┬────────┘
     └─────────────────┘             │
              │                      ▼
              │         ┌──────────────────────────┐
              │         │  Quality Assurance       │
              │         │  - Shop/Warehouse Review │
              │         │  - Packaging Review      │
              │         │  - Inventory Check       │
              │         │  - Supplier Invoices     │
              │         │  - Authenticity Proof    │
              │         └────────────┬─────────────┘
              │                      │
              │                      ▼
              │         ┌──────────────────────────┐
              │         │  Product Upload Enabled  │
              │         │  - Add Products          │
              │         │  - Compliance Check      │
              │         │  - 5+ Images Required    │
              │         └────────────┬─────────────┘
              │                      │
              │                      ▼
              │         ┌──────────────────────────┐
              │         │  Verified Seller Process │
              │         │  - Physical Inspection   │
              │         │  - Video Interview       │
              │         │  - Supplier References   │
              │         │  - Quality Audit         │
              │         └────────────┬─────────────┘
              │                      │
              │                      ▼
              │         ┌──────────────────────────┐
              │         │  VERIFIED SELLER BADGE   │
              │         │  Bronze/Silver/Gold/Plat │
              │         │  + Performance Tracking  │
              │         └──────────────────────────┘
              │
              ▼
     ┌─────────────────┐
     │  Vendor Resubmits│
     │  Corrected Docs  │
     └─────────────────┘
              │
              ▼
     (Returns to Internal Checks)
```

---

## 4. DATABASE SCHEMA CHANGES REQUIRED

### New Fields on User Model
```python
# Business Information
business_registration_number = models.CharField(max_length=50, blank=True, null=True)
business_type = models.CharField(max_length=50, choices=BUSINESS_TYPE_CHOICES, blank=True, null=True)
business_start_date = models.DateField(blank=True, null=True)
business_description = models.TextField(blank=True, null=True)
business_logo = models.ImageField(upload_to='kyc/logos/', blank=True, null=True)
tin = models.CharField(max_length=20, blank=True, null=True)

# Identity Verification
date_of_birth = models.DateField(blank=True, null=True)
nationality = models.CharField(max_length=50, blank=True, null=True)
nin = models.CharField(max_length=11, unique=True, blank=True, null=True)
bvn = models.CharField(max_length=10, unique=True, blank=True, null=True)
id_document_type = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, blank=True, null=True)
liveness_selfie = models.ImageField(upload_to='kyc/selfies/', blank=True, null=True)
passport_photo = models.ImageField(upload_to='kyc/passports/', blank=True, null=True)

# Contact
whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)

# Address
home_address = models.TextField(blank=True, null=True)
utility_bill = models.FileField(upload_to='kyc/utilities/', blank=True, null=True)

# KYC Status Tracking
kyc_stage = models.CharField(max_length=30, choices=KYC_STAGE_CHOICES, default='registration')
kyc_submitted_at = models.DateTimeField(blank=True, null=True)
kyc_approved_at = models.DateTimeField(blank=True, null=True)
```

### New Models Needed
1. `Guarantor` - Vendor guarantor information
2. `ProductCompliance` - NAFDAC/SON compliance documents
3. `KYCInternalCheck` - Admin internal verification checks
4. `QualityAssurance` - QA review records
5. `VendorPerformance` - Performance metrics tracking
6. `VerifiedSellerStatus` - Verified seller badge management
7. `ShopPhoto` - Multiple shop/warehouse photos (ForeignKey to User)

---

## 5. VIEWS & URLS REFINEMENT

### New/Modified Views Needed

| View | Purpose | URL Pattern |
|------|---------|-------------|
| `vendor_kyc_step1` | Business Information | `/vendor/kyc/business/` |
| `vendor_kyc_step2` | Identity Verification | `/vendor/kyc/identity/` |
| `vendor_kyc_step3` | Contact & Address | `/vendor/kyc/contact/` |
| `vendor_kyc_step4` | Banking & Guarantor | `/vendor/kyc/banking/` |
| `vendor_kyc_step5` | Document Upload | `/vendor/kyc/documents/` |
| `vendor_kyc_step6` | Compliance | `/vendor/kyc/compliance/` |
| `vendor_kyc_status` | KYC Status Dashboard | `/vendor/kyc/status/` |
| `admin_kyc_review` | Admin KYC Review Panel | `/admin/kyc/review/` |
| `admin_kyc_detail` | Admin KYC Detail View | `/admin/kyc/<id>/` |
| `admin_qa_review` | Admin QA Review | `/admin/qa/<id>/` |
| `admin_verified_seller` | Admin Verified Seller | `/admin/verified-seller/<id>/` |

### KYC Stage Tracking
Add a `kyc_stage` field to User model to track progress:
```python
KYC_STAGE_CHOICES = [
    ('registration', 'Registration'),
    ('business_info', 'Business Information'),
    ('identity', 'Identity Verification'),
    ('contact', 'Contact Verification'),
    ('address', 'Address Verification'),
    ('banking', 'Banking Details'),
    ('guarantor', 'Guarantor Information'),
    ('compliance', 'Product Compliance'),
    ('documents', 'Document Upload'),
    ('internal_check', 'Internal Checks (Admin)'),
    ('quality_assurance', 'Quality Assurance (Admin)'),
    ('verified_seller', 'Verified Seller'),
    ('approved', 'Fully Approved'),
    ('rejected', 'Rejected'),
]
```

---

## 6. TEMPLATES REQUIRED

### Vendor-Facing Templates
| Template | Purpose |
|----------|---------|
| `users/kyc_step_business.html` | Business information form |
| `users/kyc_step_identity.html` | Identity verification form |
| `users/kyc_step_contact.html` | Contact & address form |
| `users/kyc_step_banking.html` | Banking & guarantor form |
| `users/kyc_step_documents.html` | Document upload form |
| `users/kyc_step_compliance.html` | Product compliance form |
| `users/kyc_status.html` | KYC progress dashboard |
| `users/kyc_rejected.html` | Rejection details & resubmit |

### Admin-Facing Templates
| Template | Purpose |
|----------|---------|
| `admin_custom/kyc_review_list.html` | All pending KYC applications |
| `admin_custom/kyc_review_detail.html` | Detailed KYC review with all documents |
| `admin_custom/kyc_internal_checks.html` | Internal verification check form |
| `admin_custom/qa_review.html` | Quality assurance review form |
| `admin_custom/verified_seller_form.html` | Verified seller badge assignment |

---

## 7. IMPLEMENTATION PRIORITY MATRIX

| Priority | Stage | Effort | Impact | Dependencies |
|----------|-------|--------|--------|--------------|
| 🔴 P0 | Business Information | Medium | High | Model changes |
| 🔴 P0 | Identity Verification | High | High | Model changes, file uploads |
| 🔴 P0 | Banking (BVN) | Medium | High | API integration needed |
| 🔴 P0 | Internal Checks | High | High | Admin workflow |
| 🟡 P1 | Address Verification | Medium | Medium | File uploads |
| 🟡 P1 | Product Compliance | Medium | Medium | Model changes |
| 🟡 P1 | Contact Verification | Low | Medium | OTP service needed |
| 🟡 P1 | KYC Stage Tracking | Medium | High | Model + view changes |
| 🟢 P2 | Guarantor | Low | Low | New model |
| 🟢 P2 | Quality Assurance | Medium | Medium | Admin workflow |
| 🟢 P2 | Performance Monitoring | High | Medium | Analytics |
| 🔵 P3 | Verified Seller Badge | Medium | Low | Marketing feature |

---

## 8. API INTEGRATIONS REQUIRED

| Integration | Purpose | Stage | Priority |
|-------------|---------|-------|----------|
| NIMC API | NIN Verification | Internal Checks | P0 |
| NIBSS API | BVN Verification | Internal Checks | P0 |
| Paystack/Flutterwave | Bank Account Name Lookup | Banking | P0 |
| CAC API | Business Registration Verification | Internal Checks | P1 |
| NAFDAC API | Product Registration Verification | Compliance | P1 |
| SMS Gateway | OTP Verification | Contact | P1 |
| Email Service | Email OTP | Contact | P1 |

---

## 9. NOTIFICATION TRIGGERS

| Trigger | Notification | Channel |
|---------|-------------|---------|
| KYC Submitted | "Your KYC has been submitted for review" | In-app, Email |
| KYC Approved (Stage 1) | "Your basic KYC is approved. Proceed to upload products" | In-app, Email |
| KYC Rejected | "Your KYC was rejected. Reason: {reason}" | In-app, Email, SMS |
| QA Passed | "Quality assurance passed. You're now a verified seller!" | In-app, Email |
| QA Failed | "Quality assurance requires improvements: {notes}" | In-app, Email |
| Verified Seller Badge | "Congratulations! You've earned the {level} Verified Seller badge" | In-app, Email |
| Document Expiring | "Your {document} is expiring soon. Please renew" | In-app, Email |
| Performance Alert | "Your {metric} is below threshold ({value})" | In-app, Email |

---

## 10. CURRENT SYSTEM GAP SUMMARY

| Area | Current State | Target State | Gap |
|------|--------------|--------------|-----|
| User Model | 12 KYC fields | 35+ KYC fields | 23+ fields missing |
| KYC Form | Single page, 5 fields | Multi-step, 30+ fields | Complete rewrite needed |
| Admin Review | Basic approve/reject | Full internal checks panel | New admin views needed |
| Document Upload | 1 document (id_document) | 10+ document types | New upload infrastructure |
| Verification | Simple boolean flag | Multi-level verification | New models needed |
| Compliance | Not tracked | NAFDAC/SON tracking | New model needed |
| Guarantor | Not implemented | Full guarantor model | New model needed |
| Performance | Not tracked | Full metrics dashboard | New model + analytics |
| Verified Badge | Not implemented | Tiered badge system | New model + UI |
| OTP Verification | Not implemented | Phone + Email OTP | New service integration |
| API Integrations | None | 6+ external APIs | New integration layer |
| Notifications | Basic in-app | Multi-channel triggers | Enhancement needed |