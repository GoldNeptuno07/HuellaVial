from django.db import models

# Create your models here.
class projects(models.Model):
    name = models.CharField(max_length=50)
    creation_date = models.DateField(auto_now_add=False)