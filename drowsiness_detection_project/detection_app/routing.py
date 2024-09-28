from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    path('ws/test/', consumers.TestConsumer.as_asgi()),
    re_path(r'ws/drowsiness/$', consumers.DrowsinessConsumer.as_asgi()),
]