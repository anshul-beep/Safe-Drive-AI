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

def gen_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            print("Failed to capture frame")
            break
        else:
            if detection_active:  # Only process frames if detection is active
                try:
                    is_drowsy, ear = detector.detect_drowsiness(frame)
                    if is_drowsy:
                        cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    cv2.putText(frame, f"EAR: {ear:.2f}", (300, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    DetectionResult.objects.create(is_drowsy=is_drowsy, ear_value=ear)
                    
                except Exception as e:
                    print(f"Error in frame processing: {e}")
                    print(traceback.format_exc())
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        image_data = text_data_json['image']

        # Remove the data URL prefix
        image_data = image_data.split(',')[1]

        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(image_array, flags=cv2.IMREAD_COLOR)

        # Process the frame
        # is_drowsy, ear = detector.detect_drowsiness(frame)
        is_drowsy=True
        ear = 0.3
    
        await self.send(text_data=json.dumps({
            'type': 'drowsiness_alert',
            'is_drowsy': is_drowsy,
            'ear': ear
        }))

        # Save result to database
        DetectionResult.objects.create(is_drowsy=is_drowsy, ear_value=ear)

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
