import os
from pathlib import Path
from dotenv import load_dotenv
from decouple import config

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-3c131gb4+f&2n%w%&0*mwgr7ibso2646$!_)dgsu)h*1xfbwbq')

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'trapApp',
]

AUTH_USER_MODEL = 'trapApp.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'trapdom.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'trapApp.context_processors.cart_context',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'trapdom.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.mysql',
        'NAME':     os.environ.get('DB_NAME', 'clothing_d'),
        'USER':     os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', '2009'),
        'HOST':     os.environ.get('DB_HOST', 'localhost'),
        'PORT':     os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# ── Аутентифікація ──────────────────────────────────────────────────────────

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Google OAuth2 ────────────────────────────────────────────────────────────

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY    = config('GOOGLE_CLIENT_ID', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_CLIENT_SECRET', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE  = ['openid', 'email', 'profile']

SOCIAL_AUTH_URL_NAMESPACE = 'social'

# Порядок кроків pipeline для Google OAuth
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'trapApp.pipeline.get_username',
    'social_core.pipeline.social_auth.associate_by_email',  # якщо email вже є — прив'язує
    'trapApp.pipeline.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
)

SOCIAL_AUTH_LOGIN_REDIRECT_URL  = '/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/'
SOCIAL_AUTH_LOGIN_ERROR_URL     = '/login/'

# ── Сесії ───────────────────────────────────────────────────────────────────

SESSION_ENGINE              = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE          = 86400
SESSION_SAVE_EVERY_REQUEST  = True
SESSION_COOKIE_SECURE       = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ── Локалізація ─────────────────────────────────────────────────────────────

LANGUAGE_CODE = 'uk'
TIME_ZONE     = 'Europe/Kyiv'
USE_I18N      = True
USE_TZ        = True

# ── Статика / медіа ─────────────────────────────────────────────────────────

STATIC_URL = 'static/'
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

OPENROUTER_API_KEY = config('OPENROUTER_API_KEY', default='')
