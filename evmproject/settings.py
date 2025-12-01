"""
Django settings for evmproject project.
"""

import os
from pathlib import Path
import dj_database_url  # Needed for Render Database

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# On Render, you should ideally set this via Environment Variables
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-%=$70@b8eq$y&9!sdualerau147z-zw^56k+zbjcyw4#sgn=xl')

# SECURITY WARNING: don't run with debug turned on in production!
# This automatically turns off Debug when you are live on Render
DEBUG = 'RENDER' not in os.environ

# Allow all hosts for easy deployment, or restrict to your Render domain
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'evmapp'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Required for Static Files on Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'evmproject.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'evmproject.wsgi.application'

# --- DATABASE CONFIGURATION (SQLite Locally, PostgreSQL on Render) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# If we are on Render, 'DATABASE_URL' will be present. Use it to override default.
db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES['default'].update(db_from_env)


# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC & MEDIA FILES ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = []

# This ensures CSS works on Render
# Use this storage engine to avoid crashing on missing map files
# Standard Django storage (Fast & Safe)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- EMAIL SETTINGS (SSL Fix for Render) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465             # <--- Changed to 465
EMAIL_USE_TLS = False        # <--- Turn OFF TLS
EMAIL_USE_SSL = True         # <--- Turn ON SSL
EMAIL_TIMEOUT = 30

# Credentials
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'USE YOUR EMAIL HERE')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'USE YOUR EMAIL PASS HERE')

DEFAULT_FROM_EMAIL = 'Event Management System <USE YOUR EMAIL HERE>'
SERVER_EMAIL = 'USE YOUR EMAIL HERE'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- INTEGRATION CREDENTIALS ---
RAZORPAY_API_KEY = os.environ.get('RAZORPAY_API_KEY', 'razorpay_api_key')
RAZORPAY_API_SECRET = os.environ.get('RAZORPAY_API_SECRET', 'razorpay_api_secret')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')


# --- CSRF SETTINGS ---
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com', 'http://127.0.0.1:8000', 'http://localhost:8000']
