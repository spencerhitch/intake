import os

REPO_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

ALLOWED_HOSTS = []


INSTALLED_APPS = [
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'intake',
    'user_accounts',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_jinja',
    'invitations',
    'storages',
    'debug_toolbar',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'NAME': 'jinja',
        'BACKEND': 'django_jinja.backend.Jinja2',
        'DIRS': [
            os.path.join(REPO_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        "OPTIONS": {
            "match_extension": ".jinja",
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                'django.template.context_processors.request',
            ],
            "globals":{
                "content": "project.content.constants",
                "linkify": "project.jinja2.linkify",
                "current_local_time": "project.jinja2.current_local_time",
                "namify": "project.jinja2.namify",
                "url_with_ids": "project.jinja2.url_with_ids",
                "oxford_comma": "project.jinja2.oxford_comma",
                "humanize": "project.jinja2.humanize",
                "settings": "django.conf.settings",
            }
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
# django-allauth and django-invitations
ACCOUNT_FORMS = {
    'login': 'user_accounts.forms.LoginForm'
}
ACCOUNT_ADAPTER = 'invitations.models.InvitationsAdapter'
INVITATIONS_INVITATION_EXPIRY = 14
INVITATIONS_INVITATION_ONLY = True
INVITATIONS_SIGNUP_REDIRECT = 'account_signup'
INVITATIONS_ADAPTER = ACCOUNT_ADAPTER
ACCOUNT_EMAIL_SUBJECT_PREFIX = '' # don't prefix emails with the name of the site
INVITATIONS_EMAIL_SUBJECT_PREFIX = ACCOUNT_EMAIL_SUBJECT_PREFIX
ACCOUNT_EMAIL_VERIFICATION = "none"  # invitation only, so email confirmation is redundant
ACCOUNT_SIGNUP_PASSWORD_VERIFICATION = False  # they can always reset the password
ACCOUNT_EMAIL_REQUIRED = True  # ensure that people have emails
ACCOUNT_USERNAME_REQUIRED = False  # we don't need usernames
ACCOUNT_AUTHENTICATION_METHOD = "email"  # login using email
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 9
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 60
ACCOUNT_LOGOUT_ON_GET = True
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
ADMINS = [
    ('Ben', 'bgolder@codeforamerica.org'),
]

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
]

SITE_ID = 1


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(REPO_DIR, 'frontend', 'build'),
]
STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'
PDFPARSER_PATH = os.path.join(REPO_DIR, 'intake', 'pdfparser.jar')

