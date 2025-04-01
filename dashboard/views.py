from django.shortcuts import render, get_list_or_404
from django.utils import timezone
from datetime import timedelta
from . import models

# Create your views here.
def main_view(request):
    # Get the projects
    projects = models.projects.objects.all()
    # Get the most recent projects (projects bewteen 8 days ago and the current time)
    time = timezone.now() - timedelta(days= 16)
    recent_projects = projects.filter(creation_date__gte= time).order_by("-creation_date")
    old_projects= projects.filter(creation_date__lte= time - timedelta(days= 1)).order_by("-creation_date")
    context = {
        "recent_projects": recent_projects,
        "old_projects": old_projects,
    }
    return render(request, "dashboard/dashboard.html", context)