from django.urls import re_path
from .consumers import BirdConsumer  # Import your consumer

websocket_urlpatterns = [
    re_path(r'ws/birds/$', BirdConsumer.as_asgi()),  # WebSocket URL
]
