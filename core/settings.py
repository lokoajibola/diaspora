"""Django settings for core project."""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, True),
)
environ.Env.read_env(BASE_DIR / '.env')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

def _get_bool_env(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _get_list_env(name, default=""):
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "change-this-before-production-7f9a2c4d18b64a2f9c5e1b7a4d6f8c2e",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _get_bool_env("DJANGO_DEBUG", False)

ALLOWED_HOSTS = _get_list_env(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost,diasporaway.pythonanywhere.com",
)

CSRF_TRUSTED_ORIGINS = _get_list_env(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://diasporaway.pythonanywhere.com",
)


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "products",
    "orders",
    "axes",
    "users",
    "payments",
    "logistics",
    
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'axes.middleware.AxesMiddleware', # Add this
]

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = _get_bool_env("DJANGO_SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _get_bool_env("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
    SECURE_HSTS_PRELOAD = _get_bool_env("DJANGO_SECURE_HSTS_PRELOAD", False)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

ROOT_URLCONF = "core.urls"

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend', # Must be first to ensure it checks for lockout before allowing authentication
    'django.contrib.auth.backends.ModelBackend',
]

# Axes Configuration
AXES_FAILURE_LIMIT = 5                      # 5 attempts
AXES_COOLOFF_TIME = 24                      # 24 hours
AXES_LOCKOUT_PARAMETERS = ["ip_address"]    # Lock by IP
AXES_RESET_ON_SUCCESS = True                # Reset failures on valid login
# Add this to point Axes to your custom lockout template
AXES_LOCKOUT_TEMPLATE = 'axes/lockout.html'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.currency_processor',
                'users.context_processors.notification_count',
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

LOGIN_REDIRECT_URL = 'login_redirect'
LOGOUT_REDIRECT_URL = 'home'

# This is the key used to store the cart in the session
CART_SESSION_ID = 'cart'

SHIPPING_RATES = {
    'UK': 15000.00,   # Base NGN rate
    'USA': 20000.00,
    'Canada': 22000.00,
    'Ghana': 5000.00,
}

# For messages styling
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Base prices are stored in NGN and converted for display with these static rates.
CURRENCIES = {
    'NGN': {'name': 'Nigerian Naira', 'symbol': '₦'},
    'GHC': {'name': 'Ghana Cedi', 'symbol': 'GH₵'},
    'GBP': {'name': 'British Pound', 'symbol': '£'},
    'USD': {'name': 'US Dollar', 'symbol': '$'},
    'CAD': {'name': 'Canadian Dollar', 'symbol': 'C$'},
    'EUR': {'name': 'Euro', 'symbol': '€'},
}

EXCHANGE_RATES = {
    'NGN': 1.0,
    'GHC': 0.0085,
    'GBP': 0.00052,
    'USD': 0.00066,
    'CAD': 0.00090,
    'EUR': 0.00061,
}

PAYSTACK_PUBLIC_KEY = env('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_SECRET_KEY = env('PAYSTACK_SECRET_KEY', default='')
PAYSTACK_WEBHOOK_SECRET = env('PAYSTACK_WEBHOOK_SECRET', default=PAYSTACK_SECRET_KEY)
PAYSTACK_BASE_URL = env('PAYSTACK_BASE_URL', default='https://api.paystack.co')
PAYSTACK_CALLBACK_URL = env('PAYSTACK_CALLBACK_URL', default='')

# Email Configuration (for OTP and notifications)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@reachafrica.com')

# Twilio Configuration (for SMS and WhatsApp OTP)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', '')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
