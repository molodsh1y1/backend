import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['98.81.212.132', 'ec2-98-81-212-132.compute-1.amazonaws.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'rest_framework',
    'corsheaders',
    'constance',
    'constance.backends.database',
    'storages',

    # auth
    'oauth2_provider',
    'allauth',
    'allauth.account',
    "allauth.headless",
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.apple',

    # project
    'core',
    'dip',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',

    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'urls'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'oauth2_provider.backends.OAuth2Backend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SILENCED_SYSTEM_CHECKS = ['rest_framework.W001']

FRONTEND_URL = os.getenv('FRONTEND_URL')
BACKEND_URL = os.getenv('BACKEND_URL')

HEADLESS_ONLY = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    'http://98.81.212.132',
    'http://ec2-98-81-212-132.compute-1.amazonaws.com',
]

CORS_ALLOW_HEADERS = ("*", )
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'http://98.81.212.132',
    'http://ec2-98-81-212-132.compute-1.amazonaws.com',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'app.wsgi.application'
ASGI_APPLICATION = 'asgi.application'

REDIS_LINK = os.getenv('REDIS_LINK', 'redis:6379')
CHANNEL_LAYERS = {
    'default': {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        'CONFIG': {
            "hosts": [(REDIS_LINK.split(':')[0], int(REDIS_LINK.split(':')[1]))],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        "NAME": os.getenv('POSTGRES_DB', False),
        "USER": os.getenv('POSTGRES_APP_USER', False),
        "PASSWORD": os.getenv('POSTGRES_APP_PASSWORD', False),
        "HOST": os.getenv('POSTGRES_LINK', ':').split(":")[0],
        "PORT": os.getenv('POSTGRES_LINK', ':').split(":")[1],
        "OPTIONS": {
            "pool": {
                "min_size": 1,
                "max_size": 20,
            },
        },
    }
}


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
STATIC_ROOT = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s][%(levelname)s][%(name)s][%(funcName)s][%(lineno)s]: %(message)s'
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            'formatter': 'simple',
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    'loggers': {
        'botocore': {
            'httpx': ['console'],
            'level': 'WARN',
        },
        'urllib3': {
            'httpx': ['console'],
            'level': 'WARN',
        },
        'asyncio': {
            'httpx': ['console'],
            'level': 'WARN',
        },
        'oauthlib.oauth2.rfc6749': {
            'httpx': ['console'],
            'level': 'WARN',
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_LINK}',
    }
}

CORE_AUTH_FIXED_VERIFICATION_CODE = os.getenv('CORE_AUTH_FIXED_VERIFICATION_CODE', '000000')
CORE_AUTH_USE_FIXED_VERIFICATION_CODE = os.getenv('CORE_AUTH_USE_FIXED_VERIFICATION_CODE', 0)
CORE_AUTH_PHONE_REGISTRATION_ENABLED = True
CORE_AUTH_VERIFICATION_CODE_MAX_ATTEMPTS = 5
CORE_AUTH_VERIFICATION_CODE_LENGTH = 6
