from django.utils import timezone
from datetime import timedelta
from django.db import models

# Create your models here.
class projects(models.Model):
    name = models.CharField(max_length=50)
    creation_date = models.DateField(auto_now_add=True)

    def was_published_recently(self):
        now = timezone.now()
        return timezone.now() - timedelta(days=16) <= self.creation_date <= now