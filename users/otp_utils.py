"""
OTP Verification Utilities
- Generates 6-digit codes
- Sends via SMS (Twilio), WhatsApp (Twilio), or Email
- Verifies codes with expiry checking
"""
import random
import string
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


def generate_otp(length=6):
    """Generate a random numeric OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))


def send_sms_via_twilio(to_phone, message):
    """Send SMS via Twilio API"""
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
    
    if not all([account_sid, auth_token, from_number]):
        logger.warning(f"Twilio not configured. Would send SMS to {to_phone}: {message}")
        return False
    
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=from_number,
            to=to_phone
        )
        logger.info(f"SMS sent to {to_phone}")
        return True
    except Exception as e:
        logger.error(f"Twilio SMS failed to {to_phone}: {e}")
        return False


def send_whatsapp_via_twilio(to_phone, message):
    """Send WhatsApp message via Twilio API"""
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    whatsapp_from = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', None)
    
    if not all([account_sid, auth_token, whatsapp_from]):
        logger.warning(f"Twilio WhatsApp not configured. Would send WhatsApp to {to_phone}: {message}")
        return False
    
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=f'whatsapp:{whatsapp_from}',
            to=f'whatsapp:{to_phone}'
        )
        logger.info(f"WhatsApp sent to {to_phone}")
        return True
    except Exception as e:
        logger.error(f"Twilio WhatsApp failed to {to_phone}: {e}")
        return False


def send_email_otp(to_email, otp_code):
    """Send OTP via email using Django's email system"""
    subject = "Your ReachAfrica Verification Code"
    message = f"""
Hello,

Your ReachAfrica verification code is: {otp_code}

This code expires in 10 minutes. Please do not share this code with anyone.

If you did not request this code, please ignore this email.

Best regards,
ReachAfrica Team
"""
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 12px; padding: 30px; }}
        .header {{ text-align: center; padding-bottom: 20px; border-bottom: 2px solid #f0f0f0; }}
        .code {{ font-size: 36px; font-weight: bold; color: #198754; text-align: center; padding: 20px; 
                  letter-spacing: 8px; background: #f0fdf4; border-radius: 8px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="color: #198754;">ReachAfrica</h2>
            <p>Email Verification</p>
        </div>
        <p>Hello,</p>
        <p>Your ReachAfrica verification code is:</p>
        <div class="code">{otp_code}</div>
        <p>This code expires in <strong>10 minutes</strong>. Please do not share this code with anyone.</p>
        <p>If you did not request this code, please ignore this email.</p>
        <div class="footer">
            <p>Best regards,<br>ReachAfrica Team</p>
        </div>
    </div>
</body>
</html>
"""
    try:
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@reachafrica.com'),
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.info(f"OTP email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {e}")
        return False


def send_phone_otp(phone_number, otp_code, method='sms'):
    """
    Send OTP to phone via SMS or WhatsApp
    Returns (success: bool, message: str)
    """
    message = f"Your ReachAfrica verification code is: {otp_code}. Expires in 10 minutes."
    
    if method == 'whatsapp':
        success = send_whatsapp_via_twilio(phone_number, message)
    else:
        success = send_sms_via_twilio(phone_number, message)
    
    # Fallback: Log the OTP for development/testing
    if not success:
        logger.info(f"[DEV MODE] OTP for {phone_number}: {otp_code}")
        # In development, still "succeed" but log it
        if settings.DEBUG:
            logger.info(f"[DEV] Would send {method} to {phone_number} with code {otp_code}")
            return True, f"[DEV] OTP {otp_code} sent to {phone_number}"
        return False, "Failed to send OTP. Please try again."
    
    return True, "OTP sent successfully!"


def verify_otp(user, otp_code, otp_type='phone'):
    """
    Verify OTP code for a user
    otp_type: 'phone' or 'email'
    Returns: (is_valid: bool, message: str)
    """
    from .models import OTPVerification
    
    now = timezone.now()
    expiry_time = now - timedelta(minutes=10)
    
    # Find the latest unverified OTP
    otp_record = OTPVerification.objects.filter(
        user=user,
        otp_type=otp_type,
        is_verified=False,
        created_at__gte=expiry_time
    ).order_by('-created_at').first()
    
    if not otp_record:
        return False, "No valid OTP found. Please request a new one."
    
    if otp_record.otp_code != otp_code:
        otp_record.attempts += 1
        otp_record.save(update_fields=['attempts'])
        
        if otp_record.attempts >= 5:
            otp_record.is_expired = True
            otp_record.save(update_fields=['is_expired'])
            return False, "Too many failed attempts. Please request a new OTP."
        
        return False, "Invalid OTP code. Please try again."
    
    # Mark as verified
    otp_record.is_verified = True
    otp_record.verified_at = now
    otp_record.save(update_fields=['is_verified', 'verified_at'])
    
    # Update user's OTP verification status
    if otp_type == 'phone':
        user.otp_phone_verified = True
        user.save(update_fields=['otp_phone_verified'])
    elif otp_type == 'email':
        user.otp_email_verified = True
        user.save(update_fields=['otp_email_verified'])
    
    return True, "OTP verified successfully!"


def create_and_send_otp(user, otp_type='phone', method='sms'):
    """
    Create a new OTP record and send it
    otp_type: 'phone' or 'email'
    method: 'sms', 'whatsapp' (only for phone)
    Returns: (success: bool, message: str)
    """
    from .models import OTPVerification
    
    otp_code = generate_otp()
    now = timezone.now()
    
    # Expire any existing unverified OTPs for this user+type
    OTPVerification.objects.filter(
        user=user,
        otp_type=otp_type,
        is_verified=False
    ).update(is_expired=True)
    
    # Create new OTP record
    otp_record = OTPVerification.objects.create(
        user=user,
        otp_code=otp_code,
        otp_type=otp_type,
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    
    if otp_type == 'phone':
        success, msg = send_phone_otp(user.phone_number, otp_code, method)
    elif otp_type == 'email':
        success = send_email_otp(user.email, otp_code)
        msg = "OTP sent to email!" if success else "Failed to send email OTP."
    else:
        return False, "Invalid OTP type."
    
    if success:
        otp_record.is_sent = True
        otp_record.save(update_fields=['is_sent'])
    
    return success, msg