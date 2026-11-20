"""
Django settings for StudioGest project.
"""

import os
import sys
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env si existe
load_dotenv(BASE_DIR / '.env')

# Agregar directorio apps al sys.path para importaciones limpias
sys.path.insert(0, str(BASE_DIR / 'apps'))

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-studiogest-dev-secret-key-change-in-production'
    else:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured('SECRET_KEY debe configurarse cuando DEBUG=False.')

_allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
if _allowed_hosts:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts.split(',') if host.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
else:
    ALLOWED_HOSTS = []

# Origenes confiables para CSRF (separados por coma). En desarrollo se incluyen los locales.
_csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins.split(',') if origin.strip()]
elif DEBUG:
    CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']


# Enable the isolated business portal and public booking URLs together.
TENANT_BOOKING_ENABLED = os.getenv('TENANT_BOOKING_ENABLED', 'false').lower() == 'true'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_otp',
    'django_otp.plugins.otp_totp',
    # Aplicaciones del proyecto
    'accounts',
    'customers',
    'services',
    'appointments',
    'dashboard',
    'reports',
    'inventory',
    'sales',
]

AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'accounts.authentication.EmailBackend',
]
OTP_TOTP_ISSUER = 'StudioGest'

VERCEL_DEPLOYMENT = os.getenv('VERCEL') == '1'
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 5
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'webmaster@localhost')
ADMIN_ACCESS_ALERT_EMAIL = os.getenv('ADMIN_ACCESS_ALERT_EMAIL', '')


# Update the terms document together with its version.
TERMS_VERSION = '1.0'
PUBLIC_SITE_ORIGIN = os.getenv('PUBLIC_SITE_ORIGIN', 'https://studiogest-web-1.vercel.app').rstrip('/')

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'accounts:login'


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.idle_session.IdleSessionMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'accounts.security.PrivilegedAccessMiddleware',
    'accounts.middleware.RequireTermsAcceptance',
    'accounts.middleware.IsolateBusinessPanel',
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
                'config.seo.public_site',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# Motor de base de datos, según la variable DB_ENGINE del archivo .env:
#   mysql      -> MySQL (motor principal del proyecto)
#   postgresql -> PostgreSQL
#   sqlite     -> SQLite (valor por defecto, para desarrollo sin instalar nada)
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite').lower()

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            disable_server_side_cursors=True,
        )
    }
elif DB_ENGINE == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'studiogest_db'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
elif DB_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'studiogest_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Sesión: expiración tras 30 minutos de inactividad (RNF-04)
SESSION_COOKIE_AGE = 1800
SESSION_IDLE_SECONDS = 1800
SESSION_SAVE_EVERY_REQUEST = True

# Endurecimiento de seguridad para producción (solo cuando DEBUG=False)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    if os.getenv('VERCEL') == '1':
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'

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


# Internationalization (Colombia)
LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = (
    BASE_DIR / 'public' / 'static' if os.getenv('VERCEL') == '1' else BASE_DIR / 'staticfiles'
)

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
