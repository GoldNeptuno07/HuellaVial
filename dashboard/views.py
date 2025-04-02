from django.shortcuts import render, redirect
from django.test.utils import setup_test_environment
from django.utils import timezone
from datetime import timedelta
from . import models

# Create your views here.

"""
    Main view of the dashboard
"""
def main_view(request): 
    # Get the projects
    projects = models.projects.objects.all()
    # Get the most recent projects (projects bewteen 16 days ago and the current time)
    time = timezone.now() - timedelta(days= 16)
    recent_projects = projects.filter(creation_date__gte= time, creation_date__lte= timezone.now()).order_by("-creation_date")
    old_projects= projects.filter(creation_date__lte= time - timedelta(seconds= 1)).order_by("-creation_date")
    context = {
        "recent_projects": recent_projects,
        "old_projects": old_projects,
    }
    return render(request, "dashboard/dashboard.html", context)

"""
     Impact matrix view (tool)
"""
def impact_matrix_view(request):
    if request.method == 'POST':
        # Save the new project
        name = request.POST["project_name"]
        new_project = models.projects(name= name)
        new_project.save()
        # Redirect to the main view
        return render(request, "dashboard/matrix.html", {})

    return redirect("dashboard:main")