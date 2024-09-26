from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page  # Import gzip_page
from .drowsiness_detector import DrowsinessDetector
from .models import DetectionResult
import cv2
import traceback
import json
import requests

# Initialize the detector and global detection status
detector = DrowsinessDetector()
detection_active = False  # Toggle state

def index(request):
    return render(request, 'detection_app/index.html')

def gen_frames():
    camera = cv2.VideoCapture(0,cv2.CAP_V4L2)
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

@gzip_page  # Correct usage of gzip_page decorator
def video_feed(request):
    return StreamingHttpResponse(gen_frames(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

@csrf_exempt
def toggle_detection(request):
    global detection_active
    if request.method == 'POST':
        data = json.loads(request.body)
        detection_active = data.get('active', False)
        return JsonResponse({'status': detection_active})

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
