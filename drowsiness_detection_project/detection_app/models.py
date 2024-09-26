from django.db import models

class DetectionResult(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    is_drowsy = models.BooleanField()
    ear_value = models.FloatField()
