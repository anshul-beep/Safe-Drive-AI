import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .drowsiness_detector import DrowsinessDetector
import base64
import cv2
import numpy as np

class DrowsinessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.detector = DrowsinessDetector()

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
        is_drowsy, ear = self.detector.detect_drowsiness(frame)

        if is_drowsy:
            await self.send(text_data=json.dumps({
                'type': 'drowsiness_alert',
                'is_drowsy': is_drowsy,
                'ear': ear
            }))


# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        await self.send(text_data=json.dumps({
            'message': 'Hello WebSocket!',
        }))
