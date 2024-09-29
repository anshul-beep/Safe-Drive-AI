from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .drowsiness_detector import DrowsinessDetector
from .models import DetectionResult
import cv2
import numpy as np
import base64
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio

detector = DrowsinessDetector()

def index(request):
    return render(request, 'detection_app/index.html')

class DrowsinessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            image_data = text_data_json['image']

            # Remove the data URL prefix and decode base64 image
            image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            frame = cv2.imdecode(image_array, flags=cv2.IMREAD_COLOR)

            # Process the frame
            is_drowsy = True
            ear = 0.3

            await self.send(text_data=json.dumps({
                'type': 'drowsiness_alert',
                'is_drowsy': is_drowsy,
                'ear': ear
            }))

            # Save result to database
            DetectionResult.objects.create(is_drowsy=is_drowsy, ear_value=ear)

            # Clear image-related data to free memory
            del frame
            del image_bytes
            del image_array

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
            # Ensure memory is still cleared even in case of an exception
            del frame
            del image_bytes
            del image_array


@csrf_exempt
def toggle_detection(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        active = data.get('active', False)
        # You can add any server-side logic here if needed
        return JsonResponse({'status': 'success', 'active': active})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def nearby_places(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    
    API_KEY = 'YOUR_GOOGLE_PLACES_API_KEY'
    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=500&type=rest_area&key={API_KEY}'
    
    try:
        response = requests.get(url)
        places_data = response.json()
        
        places = [place['name'] for place in places_data.get('results', [])]
        return JsonResponse({'places': places})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)