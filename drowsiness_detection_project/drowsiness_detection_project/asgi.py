import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from drowsiness_detection_project.detection_app.consumers import DrowsinessConsumer  # Adjust this import as necessary
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drowsiness_detection_project.settings')

# Get the Django ASGI application
django_asgi_app = get_asgi_application()

# Define your WebSocket URL patterns
websocket_urlpatterns = [
    path('ws/drowsiness/', DrowsinessConsumer.as_asgi()),
]

# Define the ASGI application
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # Handle HTTP requests with Django
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
