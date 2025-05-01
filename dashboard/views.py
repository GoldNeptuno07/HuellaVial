from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
from . import models

import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

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

        operations= [
            request.POST.getlist("preparation[]"),
            request.POST.getlist("construction[]"),
            request.POST.getlist("maintenance[]"),
        ]

        project = models.projects.objects.create(name=name)
        
        # Create default phases
        for i, phase_name in enumerate(['preparacion', 'construccion', 'operacion']):
            new_phase= models.phase.objects.create(id_project=project, name=phase_name)
            # Add the corresponding operations of "each" phase (convert them to lowercase)
            for operation in operations[i]:
                models.operation.objects.create(id_phase= new_phase, name= operation.lower())
            # Add default ratings for each subresource in the current phase
            for subresource in models.subresource.objects.all():
                models.rating.objects.create(id_phase= new_phase, id_subresource= subresource)

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
    
    context = {
        "project": project,
        "phases": project.phases.all(),
        "phase": current_phase,
        "operations": operations,
        "resources": resources,
    }
    return render(request, "dashboard/matrix.html", context)

@require_POST
def toggle_impact(request):
    """
        Function to create or update an impact made by an operation
        to a certain subresource.
    """
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

@require_POST
def update_rating(request, rating_id):
    """
        Function to update the damage rate of a certain
        subresource based on the operation. 
    """
    if request.method == "POST":
        try:
            field = request.POST.get('field')
            value = request.POST.get('value')
            r = models.rating.objects.get(pk=rating_id)
            setattr(r, field, value)
            r.save()
            return JsonResponse({"status": "ok"})
        except rating.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Rating not found"}, status=404)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@require_POST
def add_operation(request, phase_id):
    if request.method == "POST":
        action= request.POST.get('action')
        phase= models.phase.objects.get(pk= phase_id)
        name= request.POST.get('operation_name').lower()
        description= request.POST.get('operation_description')

        exists= models.operation.objects.filter(name= name).exists()

        if action == "0" and exists: # Remove if it exists
            models.operation.objects.get(name= name).delete()
        elif action == "1" and not exists: # Add if it doesn't exists
            models.operation.objects.create(id_phase= phase, name= name, description= description)

        return redirect('dashboard:impact-matrix', project_id= phase.id_project.id, phase_name= phase.name)

@require_POST
def update_description(request, rating_id):
    if request.method == 'POST':
        description= request.POST.get('description')

        rating_obj= models.rating.objects.get(pk= rating_id)
        setattr(rating_obj, 'description', description)
        rating_obj.save()

        return JsonResponse({"status": "ok"})


"""
    Iterate a long the proyect ratings and get all the operations 
    that have a marked impact and affect the current rating subresource.

    - Finished the prompt...

        Example.
                Nombre. Carretera 1
                Fases. 
                    - Preparacion.
                        * Calidad del Agua.
                            - Limpieza
                            - Generacion de Acuoeductos
                            # Calificaciones. 
                                - Intensidad. 4
                                - Importance. 3
                                - Extension. 1
                                - Persistence. 5
                                etc...
                        * Calidad de la Tierra.
                            - Aplanar terreno
                            # Calificaciones. 
                                etc...
                    - Construccion.
                        * Calidad del Agua.
                            - Desarrollo de vias subterraneas
                            # Calificaciones. 
                                etc...
                        * Calidad de la Tierra.
                            - Excabaciones
                            # Calificaciones. 
                                etc...
                    - Mantenimiento 
                        etc...
"""
def getMarkedImpactsInSubresource(rating_obj):
    """
        Get all the operations that damage an especific subresource
    """
    subresource_obj= rating_obj.id_subresource
    impacts= subresource_obj.impacts.filter(is_marked= True) # If it's marked then it damages
    
    # Get all the marked operations
    operation_ids= impacts.values_list('id_operation', flat= True) 
    
    # Return the marked operations of the current phase
    return rating_obj.id_phase.operations.filter(id__in= operation_ids).distinct() 


def generate_report(request, project_id):
    project= models.projects.objects.get(pk= project_id)

    prompt= f""" 
            Nombre. {project.name}\n
        """

    phases= project.phases.all()
    operations_per_phase= []
    for phase in phases: # Project phases
        operations= []
        prompt += f"\t* Fase. {phase.name}\n"

        any_operation= False
        for rating in phase.ratings.all():

            operations= getMarkedImpactsInSubresource(rating)
            
            # If there's no operation that damage the current
            # subresource then skip the ratings
            if len(operations) == 0: continue
            else: any_operation= True

            # Adding subresource name
            prompt += f"\t\t\t- {rating.id_subresource.name}\n"
            # Adding Operations
            for operation in operations:
                prompt += f"\t\t\t\t* {operation.name}\n"
            # Adding ratings
            prompt += "\t\t\t\t# Calificaciones\n"
            prompt += f"\t\t\t\t\t- Intensidad. {rating.intensity}\n"
            prompt += f"\t\t\t\t\t- Importancia. {rating.importance}\n"
            prompt += f"\t\t\t\t\t- Extension. {rating.extension}\n"
            prompt += f"\t\t\t\t\t- Reversibilidad. {rating.reversibility}\n"
        
        if not any_operation: prompt += f"\t\t\t\t-- No hay operaciones...\n"

    """
        Implement a secure connection with azure services 
    """
    # Code...

    return HttpResponse(prompt)

