import cv2
import dlib
import numpy as np
from scipy.spatial import distance
import os
from django.conf import settings
import winsound  # For sound alerts on Windows

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

class DrowsinessDetector:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        predictor_path = os.path.join(settings.BASE_DIR, "models\shape_predictor_68_face_landmarks.dat")
        if not os.path.exists(predictor_path):
            raise FileNotFoundError(f"Predictor file not found at {predictor_path}")
        self.predictor = dlib.shape_predictor(predictor_path)
        self.EYE_AR_THRESH = 0.25  # Adjusted for sensitivity
        self.EYE_AR_CONSEC_FRAMES = 15  # Reduced for quicker alerts
        self.COUNTER = 0
        self.ALARM_ON = False

    def detect_drowsiness(self, frame):
        if frame is None or frame.size == 0:
            print("Empty frame received")
            return False, 0.0

        print(f"Original frame shape: {frame.shape}, dtype: {frame.dtype}")

        # Convert to RGB (dlib expects RGB)
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            print(f"Unexpected frame format: shape {frame.shape}")
            return False, 0.0

        # Ensure the image is 8-bit
        if rgb_frame.dtype != np.uint8:
            rgb_frame = (rgb_frame * 255).astype(np.uint8)

        # Resize the frame for faster processing
        height, width = rgb_frame.shape[:2]
        if width > 320:
            scaling_factor = 300.0 / width
            rgb_frame = cv2.resize(rgb_frame, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

        # Detect faces in the RGB frame
        try:
            faces = self.detector(rgb_frame, 0)
            print(f"Detected {len(faces)} faces")
        except Exception as e:
            print(f"Error in face detection: {e}")
            return False, 0.0

        for face in faces:
            try:
                landmarks = self.predictor(rgb_frame, face)

                left_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(36, 42)]
                right_eye = [(landmarks.part(n).x, landmarks.part(n).y) for n in range(42, 48)]

                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)

                ear = (left_ear + right_ear) / 2.0

                # Drowsiness detection logic
                if ear < self.EYE_AR_THRESH:
                    self.COUNTER += 1
                    if self.COUNTER >= self.EYE_AR_CONSEC_FRAMES:
                        self.ALARM_ON = True
                        self.alert()
                        return True, ear
                else:
                    self.COUNTER = 0
                    self.ALARM_ON = False
            except Exception as e:
                print(f"Error in landmark detection or EAR calculation: {e}")

        return False, ear if 'ear' in locals() else 0.0

    def alert(self):
        # Visual alert in the frame (this should be done in the view, not here)
        print("Drowsiness detected! Activating alarm...")
        # Sound alert
        frequency = 2500  # Set Frequency To 2500 Hertz
        duration = 1000   # Set Duration To 1000 ms == 1 second
        winsound.Beep(frequency, duration)  # Beep sound for alert

