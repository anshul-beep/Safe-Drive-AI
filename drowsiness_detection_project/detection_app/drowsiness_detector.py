import cv2
import dlib
import numpy as np
from scipy.spatial import distance
import os
from django.conf import settings
import pygame
import logging
import gc
import psutil

logger = logging.getLogger(__name__)

# Function to log memory usage (optional but useful for tracking memory)
def log_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    logger.info(f"Memory usage: RSS={mem_info.rss / (1024 * 1024)} MB")

# Function to calculate eye aspect ratio
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

class DrowsinessDetector:
    def __init__(self):
        # Initialize the face detector and shape predictor
        self.detector = dlib.get_frontal_face_detector()
        predictor_path = os.path.join(settings.BASE_DIR, "models/shape_predictor_68_face_landmarks.dat")
        if not os.path.exists(predictor_path):
            raise FileNotFoundError(f"Predictor file not found at {predictor_path}")
        self.predictor = dlib.shape_predictor(predictor_path)
        self.EYE_AR_THRESH = 0.25
        
        # Initialize Pygame and load alert sound
        pygame.mixer.init()
        self.alert_sound = os.path.join(settings.BASE_DIR, 'models/Alert (1).wav')
        if not os.path.exists(self.alert_sound):
            raise FileNotFoundError(f"Alert sound file not found at {self.alert_sound}")

    def detect_drowsiness(self, frame):
        # Log memory usage at the start of each frame processing (optional)
        log_memory_usage()

        logger.info(f"Received frame: type={type(frame)}, shape={frame.shape if hasattr(frame, 'shape') else 'N/A'}")
        if frame is None or not hasattr(frame, 'size') or frame.size == 0:
            logger.warning("Empty or invalid frame received")
            return False, 0.0

        # Convert frame to RGB if it's in BGR format
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = None  # Free the original BGR frame to save memory
        else:
            logger.warning(f"Unexpected frame format: shape {frame.shape}")
            return False, 0.0

        # Ensure frame is in uint8 format
        if rgb_frame.dtype != np.uint8:
            rgb_frame = (rgb_frame * 255).astype(np.uint8)

        # Resize the frame for faster processing if the width is larger than 320
        height, width = rgb_frame.shape[:2]
        if width > 320:
            scaling_factor = 320.0 / width
            rgb_frame = cv2.resize(rgb_frame, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

        try:
            faces = self.detector(rgb_frame, 0)
            logger.info(f"Detected {len(faces)} faces")
            if len(faces) == 0:
                logger.info("No faces detected in this frame")
                return False, 0.0
        except Exception as e:
            logger.error(f"Error in face detection: {e}")
            rgb_frame = None  # Free memory
            return False, 0.0

        # Loop over detected faces
        for face in faces:
            try:
                landmarks = self.predictor(rgb_frame, face)

                # Get coordinates of eyes
                left_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
                right_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]

                # Calculate EAR (Eye Aspect Ratio) for both eyes
                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)

                # Average EAR for both eyes
                ear = (left_ear + right_ear) / 2.0
                logger.info(f"Left EAR: {left_ear}, Right EAR: {right_ear}, Average EAR: {ear}")

                # If the EAR is below the threshold, drowsiness is detected
                if ear < self.EYE_AR_THRESH:
                    logger.info(f"Drowsiness detected! EAR: {ear}")
                    self.alert()  # Play the alert sound
                    return True, ear
                else:
                    logger.info(f"EAR above threshold: {ear}")

            except Exception as e:
                logger.error(f"Error in landmark detection or EAR calculation: {e}")

        # Free memory after processing each frame
        rgb_frame = None
        gc.collect()  # Explicitly call garbage collector

        return False, ear

    def alert(self):
        logger.info("Drowsiness detected! Activating alarm...")
        try:
            if not pygame.mixer.music.get_busy():  # Only load and play if no sound is currently playing
                pygame.mixer.music.load(self.alert_sound)
                pygame.mixer.music.play()
                logger.info("Alert sound played.")
        except Exception as e:
            logger.error(f"Error playing sound: {e}")
