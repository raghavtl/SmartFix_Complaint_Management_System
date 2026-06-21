import os
import sys
import json
import time
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def _debug_log(hypothesis_id, location, message, data=None, run_id='initial'):
    # #region agent log
    payload = {
        'sessionId': '264829',
        'runId': run_id,
        'hypothesisId': hypothesis_id,
        'location': location,
        'message': message,
        'data': data or {},
        'timestamp': int(time.time() * 1000),
    }
    with open(BASE_DIR / 'debug-264829.log', 'a', encoding='utf-8') as log_file:
        log_file.write(json.dumps(payload) + '\n')
    # #endregion


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {'1', 'true', 'yes', 'on'}


def env_list(name, default=''):
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'smartfix-prod-default-8m3$Qv71xL4!pR2zN9#tK6@wH5^cY0uD1sB7fG4jM',
)

RUNNING_DEV_SERVER = any(arg.startswith('runserver') for arg in sys.argv)
# SECURITY WARNING: don't run with debug turned on in production!
# Default DEBUG=True for local runserver so static/admin assets load reliably.
DEBUG = env_bool('DJANGO_DEBUG', RUNNING_DEV_SERVER)
ENABLE_PRODUCTION_SECURITY = not DEBUG and not RUNNING_DEV_SERVER
_debug_log('H6', 'config/settings.py:42', 'settings loaded', {
    'debug': DEBUG,
    'running_dev_server': RUNNING_DEV_SERVER,
    'python_executable': sys.executable,
    'cwd': os.getcwd(),
})

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom Apps
    'complaints', 
    
    # Third Party Apps
]

# Crispy Forms Config
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploaded images)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Authentication Redirects
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Deployment security defaults. These stay enabled for deploy checks,
# but local `runserver` uses normal HTTP without forcing HTTPS.
SECURE_HSTS_SECONDS = int(
    os.getenv('DJANGO_SECURE_HSTS_SECONDS', '31536000' if ENABLE_PRODUCTION_SECURITY else '0')
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    'DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS',
    ENABLE_PRODUCTION_SECURITY,
)
SECURE_HSTS_PRELOAD = env_bool(
    'DJANGO_SECURE_HSTS_PRELOAD',
    ENABLE_PRODUCTION_SECURITY,
)
SECURE_SSL_REDIRECT = env_bool(
    'DJANGO_SECURE_SSL_REDIRECT',
    ENABLE_PRODUCTION_SECURITY,
)
SESSION_COOKIE_SECURE = env_bool(
    'DJANGO_SESSION_COOKIE_SECURE',
    ENABLE_PRODUCTION_SECURITY,
)
CSRF_COOKIE_SECURE = env_bool(
    'DJANGO_CSRF_COOKIE_SECURE',
    ENABLE_PRODUCTION_SECURITY,
)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Email backend for password reset and notifications
EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DJANGO_DEFAULT_FROM_EMAIL', 'no-reply@smartfix.local')

# Optional SMS webhook configuration for production alerting.
SMS_WEBHOOK_URL = os.getenv('DJANGO_SMS_WEBHOOK_URL', '')
SMS_AUTH_TOKEN = os.getenv('DJANGO_SMS_AUTH_TOKEN', '')
SMS_SENDER_ID = os.getenv('DJANGO_SMS_SENDER_ID', 'SmartFix')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
