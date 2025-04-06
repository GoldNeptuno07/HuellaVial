from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
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
def impact_matrix_view(request, project_id: int = None, phase_name: str = None):
    if request.method == 'POST':
        # Handle new project creation
        name = request.POST.get("project_name")
        project = models.projects.objects.create(name=name)
        
        # Create default phases
        for phase_name in ['preparacion', 'construccion', 'operacion']:
            models.phase.objects.create(id_project=project, name=phase_name)
            
        # Redirect to the first phase
        first_phase = project.phases.first()
        return redirect('dashboard:impact-matrix', 
                      project_id=project.id,
                      phase_name=first_phase.name)
    
    # GET request handling
    project = get_object_or_404(models.projects, pk=project_id)
    current_phase = get_object_or_404(models.phase, id_project=project, name=phase_name)
    
    # Prefetch related data for performance
    operations = current_phase.operations.all().prefetch_related('impact_set')
    resources = models.resource.objects.all().prefetch_related('subresources')
    
    # Prepare impact data
    impact_data = {}
    for operation in operations:
        for subresource in models.subresource.objects.all():
            impact_data[f"{operation.id}-{subresource.id}"] = operation.impact_set.filter(
                id_subresource=subresource,
                is_marked=True
            ).exists()
    
    context = {
        "project": project,
        "phases": project.phases.all(),
        "phase": current_phase,
        "operations": operations,
        "resources": resources,
        "impact_data": impact_data,
    }
    return render(request, "dashboard/matrix.html", context)

@require_POST
def toggle_impact(request):
    operation_id = request.POST.get('operation_id')
    subresource_id = request.POST.get('subresource_id')
    
    impact_obj, created = models.impact.objects.get_or_create(
        id_operation_id=operation_id,
        id_subresource_id=subresource_id,
        defaults={'is_marked': True}
    )
    
    if not created:
        impact_obj.is_marked = not impact_obj.is_marked
        impact_obj.save()
    
    return JsonResponse({
        'status': 'success',
        'is_marked': impact_obj.is_marked
    })