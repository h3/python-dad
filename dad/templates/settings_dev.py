import os, sys
from %(project_name)s.settings import *

# sys.path.append("../contrib/")
sys.path.append("../")

DEV = True
DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(
                os.path.abspath(__file__)), 'dev.db'),
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

