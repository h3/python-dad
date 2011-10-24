import os, sys
from %(project_name)s.settings import *

# sys.path.append("../contrib/")
sys.path.append("../")

DEV = True
DEBUG = True
DEBUG_TOOLBAR = False
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(
                os.path.abspath(__file__)), 'dev.db'),
    },
#   'default': {
#       'ENGINE': 'django.db.backends.mysql',
#       'NAME': '',
#       'USER': '',
#       'PASSWORD': '',
#       'HOST': '',
#       'PORT': '',
#   },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#TEMPLATE_STRING_IF_INVALID = '{{ Variable not found }}'

if DEBUG_TOOLBAR:
    INTERNAL_IPS = ('127.0.0.1', '192.168.1.103')
    INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar',)
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + ('debug_toolbar.middleware.DebugToolbarMiddleware',)
