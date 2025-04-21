"""
WSGI config for ai_agent project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# Add the app directory to the Python path
app_path = os.path.dirname(os.path.abspath(__file__))
project_path = os.path.dirname(app_path)
sys.path.append(project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_agent.settings')

try:
    application = get_wsgi_application()
except Exception as e:
    print(f"Error loading WSGI application: {e}", file=sys.stderr)
    raise
