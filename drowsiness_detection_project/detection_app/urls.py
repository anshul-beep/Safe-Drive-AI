from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('video_feed/', views.video_feed, name='video_feed'),
    path('toggle_detection/', views.toggle_detection, name='toggle_detection'),  # Add this line
    path('nearby_places/', views.nearby_places, name='nearby_places'),
]

