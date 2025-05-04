from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.projects)
admin.site.register(models.phase)
admin.site.register(models.operation)
admin.site.register(models.resource)
admin.site.register(models.subresource)
admin.site.register(models.impact)
admin.site.register(models.rating)
admin.site.register(models.reports)
