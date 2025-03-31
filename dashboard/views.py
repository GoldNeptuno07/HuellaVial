from django.shortcuts import render
from . import models

# Create your views here.
def main_view(request):
    # Get the projects
    projects = models.projects.objects.all()
    context = {
        "projects": projects
    }
    return render(request, "dashboard/dashboard.html", context)