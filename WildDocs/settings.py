"""
Django settings for WildDocs project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url
from urllib.parse import urlparse # render deployment

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables (always point to the project-level .env)
if os.environ.get("RENDER", "").lower() != "true": # render deployment
    load_dotenv(BASE_DIR / ".env", override=True) # render deployment

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-0y$vp&@l-h)yylg#lr2e9h!d9+$p9*)@96(f8lh+b24xmt0*@0')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Security (production)
if os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True").lower() == "true":
 SECURE_SSL_REDIRECT = True
 SESSION_COOKIE_SECURE = True
 CSRF_COOKIE_SECURE = True
 
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()] # render deployment
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()] # render deployment

# Static files (WhiteNoise)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'anymail',
    "accounts",
    "index",
    "dashboard",
    "request",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # render deployment
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# WhiteNoise: serve compressed static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage" # render deployment

ROOT_URLCONF = 'WildDocs.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "index/templates",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'WildDocs.wsgi.application'


# Database configuration using Supabase Session Pooler
DATABASES = {
    "default": dj_database_url.config(
        default=(os.getenv('DATABASE_URL') or "sqlite:///db.sqlite3"),
        conn_max_age=600,  # persistent connections
        # Only enforce SSL when using a Postgres DATABASE_URL. If no
        # DATABASE_URL is set we fall back to sqlite and must not pass
        # postgres-specific options (like sslmode) to sqlite's
        # Connection constructor which will raise a TypeError.
        ssl_require=True if os.getenv('DATABASE_URL', '').startswith('postgres') else False
    )
}


# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "index/static",
    BASE_DIR / "dashboard/static",
    BASE_DIR / "request/static",
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media (legacy local uploads are still referenced, so serve them in dev)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'




# Email configuration for forgot password reset
# Use Mailtrap API (works on Render free tier - SMTP is blocked)
MAILTRAP_API_TOKEN = os.getenv('MAILTRAP_API_TOKEN', '')

if MAILTRAP_API_TOKEN:
    # Use Mailtrap HTTP API (bypasses SMTP port blocking)
    EMAIL_BACKEND = 'anymail.backends.mailtrap.EmailBackend'
    ANYMAIL = {
        'MAILTRAP_API_TOKEN': MAILTRAP_API_TOKEN,
    }
else:
    # Fallback to SMTP for local development
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'hello@demomailtrap.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Logging for email debugging in production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}