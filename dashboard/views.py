from django.shortcuts import render, redirect, get_object_or_404
from django.test.utils import setup_test_environment
from django.utils import timezone
from datetime import timedelta
from . import models

# Create your views here.

"""
    Login View
"""
def login_view(request):
    pass


"""
    Log Out
"""
def logout(request):
    # Log out the user
    if request.user.is_authenticated:
        logout(request)
    return redirect("dashboard:main")



"""
    Main view of the dashboard
"""
def main_view(request): 
    # Get the projects
    projects = models.projects.objects.all()
    # Get the most recent projects (projects created 16 days ago and up to now)
    time = timezone.now() - timedelta(days= 16)
    # Order recent projects by creation date
    recent_projects = projects.filter(creation_date__gte= time, creation_date__lte= timezone.now()).order_by("-creation_date")
    # Order old projects by creation date
    old_projects= projects.filter(creation_date__lte= time - timedelta(seconds= 1)).order_by("-creation_date")                 
    context = {
        "recent_projects": recent_projects,
        "old_projects": old_projects,
    }
    return render(request, "dashboard/dashboard.html", context)

"""
     Impact matrix view (tool)
"""
def impact_matrix_view(request, project_id: int= None, phase_name: str= None):
    if request.method == 'POST':
        # Save the new project
        name = request.POST["project_name"]
        project = models.projects(name= name)
        project.save()
        # Add the default phases of the project
        for phase in ['operacion','construccion','preparacion']:
            current_phase = models.phase.objects.create(id_project= new_project, name= phase)
    else:
        project = get_object_or_404(models.projects, pk= project_id)

    # Get project's phases
    phases = project.phases.all()
    current_phase = phases.get(name= phase_name)
    # 
    
    # Add objects to context
    context = {
        "project": project,
        "phases": phases,
        "phase": current_phase,
    }
    # Redirect to the impact matrix view
    return render(request, "dashboard/matrix.html", context)