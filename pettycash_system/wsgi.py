
import os
import sys

# Add your project path
path = '/home/TRACY205/pettycash_clean'
if path not in sys.path:
    sys.path.append(path)

# Point to your Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'pettycash_system.settings'

# Load Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


"""
WSGI config for pettycash_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pettycash_system.settings')

application = get_wsgi_application()
