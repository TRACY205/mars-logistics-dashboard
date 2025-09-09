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

