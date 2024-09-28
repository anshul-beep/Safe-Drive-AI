import json
import cv2
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
from .drowsiness_detector import DrowsinessDetector
import logging

logger = logging.getLogger(__name__)

class DrowsinessConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        logger.info("WebSocket connection established")
        self.detector = DrowsinessDetector()

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if bytes_data:
                logger.info(f"Received binary data of length: {len(bytes_data)}")
                frame = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                is_drowsy, ear = self.detector.detect_drowsiness(frame)
                
                await self.send(text_data=json.dumps({
                    'type': 'drowsiness_alert',
                    'is_drowsy': is_drowsy,
                    'ear': ear
                }))
                logger.info(f"Sent drowsiness data: is_drowsy={is_drowsy}, ear={ear}")
            elif text_data:
                logger.info(f"Received text data: {text_data}")
                # Handle text data if needed
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))