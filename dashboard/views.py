from django.shortcuts import render, get_list_or_404
from . import models

# Create your views here.
def main_view(request):
    # Get the projects
    projects = get_list_or_404(models.projects)
    #projects = models.projects.objects.all()
    context = {
        "projects": projects
    }
    return render(request, "dashboard/dashboard.html", context)