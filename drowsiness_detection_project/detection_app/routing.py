from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/drowsiness/$', consumers.DrowsinessConsumer.as_asgi()),  # Make sure this matches the WebSocket URL
]
