from django.utils import timezone
from datetime import timedelta
from django.db import models

# Create your models here.

"""
    Models to store the details of the projects
"""
class projects(models.Model):
    name= models.CharField(max_length=50)
    creation_date= models.DateField(auto_now_add=True)

    def was_published_recently(self):
        now = timezone.now()
        return timezone.now() - timedelta(days=16) <= self.creation_date <= now

    def __str__(self):
        return "<Project {}>".format(self.name)

class phase(models.Model):
    id_project= models.ForeignKey(projects, on_delete= models.CASCADE, related_name= "phases")
    name= models.CharField(max_length= 50)

    def __str__(self):
        return "<Project Phase {}>".format(self.name)

class operation(models.Model):
    id_phase= models.ForeignKey(phase, on_delete= models.CASCADE, related_name= "operations")
    name= models.CharField(max_length= 50)
    description= models.CharField(max_length= 100, default= "NA")

    def __str__(self):
        return self.name

class resource(models.Model):
    name= models.CharField(max_length= 50)

    def __str__(self):
        return self.name

class subresource(models.Model):
    id_resource= models.ForeignKey(resource, on_delete= models.CASCADE, related_name= "subresources")
    name= models.CharField(max_length= 50)

    def __str__(self):
        return "<subresource {}>".format(self.name)

class impact(models.Model):
    id_operation = models.ForeignKey(operation, on_delete=models.CASCADE, related_name= 'impacts')
    id_subresource = models.ForeignKey(subresource, on_delete=models.CASCADE, related_name= 'impacts')
    is_marked = models.BooleanField(default=False)  # New field to track X marks
    observation = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ('id_operation', 'id_subresource')  # Prevent duplicates

    def __str__(self):
        return "<impact object>"

class rating(models.Model):
    class rating_scale(models.IntegerChoices):
        MINIMA= 1
        MODERADA= 2
        ALTA= 3
        # Missing the scale 4
        MUY_ALTA= 5
    
    id_phase= models.ForeignKey(phase, on_delete= models.CASCADE, related_name= 'ratings')
    id_subresource= models.ForeignKey(subresource, on_delete= models.CASCADE)
    intensity= models.IntegerField(choices= rating_scale, default= 1)
    importance= models.IntegerField(choices= rating_scale, default= 1)
    extension= models.IntegerField(choices= rating_scale, default= 1)
    persistence= models.IntegerField(choices= rating_scale, default= 1)
    reversibility= models.IntegerField(choices= rating_scale, default= 1)
    description= models.CharField(max_length= 200, default= 'NA')

    def __str__(self):
        return "<rating object>"