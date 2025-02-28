"""
ASGI config for birdnet project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from BirdNET_UI import routing  # Import your routing configuration

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'birdnet.settings')
django_asgi_app = get_asgi_application()

# application = get_asgi_application()
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns  # Add your WebSocket URL patterns
        )
    ),
})