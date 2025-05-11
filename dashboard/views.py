from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
from . import models

from openai import AzureOpenAI

import os
from dotenv import load_dotenv
import markdown2


# =======================================
# Azure Services
# =======================================
load_dotenv()

endpoint = os.getenv("ENDPOINT")
model_name = os.getenv("MODEL_NAME")
deployment = os.getenv("MODEL_NAME") + "-2"

subscription_key = os.getenv("API_KEY")
api_version = os.getenv("API_VERSION")

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)


# =======================================
# HTTP Views
# =======================================
def login_view(request):
    pass

def logout(request):
    # Log out the user
    if request.user.is_authenticated:
        logout(request)
    return redirect("dashboard:main")

def main_view(request): 
    projects = models.projects.objects.all()

    # Get the most recent and old projects:
    # recent. projects created 16 days ago and up to now
    # old. projects created more than 16 days ago

    time = timezone.now() - timedelta(days= 16)
    recent_projects = projects.filter(creation_date__gte= time, creation_date__lte= timezone.now()).order_by("-creation_date") # Order by creation date
    old_projects= projects.filter(creation_date__lte= time - timedelta(seconds= 1)).order_by("-creation_date")                 
    context = {
        "recent_projects": recent_projects,
        "old_projects": old_projects,
    }
    return render(request, "dashboard/dashboard.html", context)


def impact_matrix_view(request, project_id: int = None, phase_name: str = None):
    # Creating and initializing new project
    if request.method == 'POST':
        name = request.POST.get("project_name")
        operations= [
            request.POST.getlist("preparation[]"),
            request.POST.getlist("construction[]"),
            request.POST.getlist("maintenance[]"),
        ]
        project = models.projects.objects.create(name=name)

        # Insert phases, operations and ratings for the new project
        for i, phase_name in enumerate(['preparacion', 'construccion', 'operacion']):
            new_phase= models.phase.objects.create(id_project=project, name=phase_name)
            for operation in operations[i]:
                models.operation.objects.create(id_phase= new_phase, name= operation.lower())
            for subresource in models.subresource.objects.all():
                models.rating.objects.create(id_phase= new_phase, id_subresource= subresource)

        # Redirect back to the matrix view (phase. Preparacion)
        first_phase = project.phases.first()
        return redirect('dashboard:impact-matrix', 
                      project_id=project.id,
                      phase_name=first_phase.name)
    
    # Get a project's information
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


# =======================================
# APIs
# =======================================

@require_POST
def toggle_impact(request):
    # Function to create or update an impact (user checks a cell)
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
    # Function to update the ratings in the database 
    # (user updates the ratings in the matrix)

    if request.method == "POST":
        try:
            field = request.POST.get('field')
            value = request.POST.get('value')
            rating = models.rating.objects.get(pk=rating_id)
            setattr(rating, field, value)
            rating.save()
            return JsonResponse({"status": "ok"})
        except rating.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Rating not found"}, status=404)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@require_POST
def add_operation(request, phase_id):
    # Insert a new operation in the current project's phase if
    # it doesn't exists, else remove the operation. 

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
    # Edit the rating's description in the database

    description= request.POST.get('description')
    rating_obj= models.rating.objects.get(pk= rating_id)
    setattr(rating_obj, 'description', description)
    rating_obj.save()

    return JsonResponse({"status": "ok"})


def getMarkedImpactsInSubresource(rating_obj):
    # Get all the operations that damage an especific subresource

    subresource_obj= rating_obj.id_subresource
    impacts= subresource_obj.impacts.filter(is_marked= True) # If it's marked then it damages    
    operation_ids= impacts.values_list('id_operation', flat= True) 
    
    return rating_obj.id_phase.operations.filter(id__in= operation_ids).distinct() 

def generate_prompt(project):
    # Generate a prompt with the matrix information
    # that will be passed to a model in the cloud

    prompt= f""" 
                Nombre. {project.name}\n
            """
    # Get all the project phases & operations
    phases= project.phases.all()
    for phase in phases:
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
            prompt += f"\t\t\t\t\t- Persistencia. {rating.persistence}\n"
            prompt += f"\t\t\t\t\t- Reversibilidad. {rating.reversibility}\n"
        
        if not any_operation: 
            prompt += f"\t\t\t\t-- No hay operaciones...\n"

    return prompt

def generate_report(request, project_id):
    # Make the request to the service in the cloud 

    project= models.projects.objects.get(pk= project_id)

    # If the report has already been generated,
    # retrieve it from the database, else make the 
    # response to generate the report
    report= models.reports.objects.filter(id_project= project) 
    if report.exists():
        model_response= "".join([obj.content for obj in report])

    else:
        prompt= generate_prompt(project)
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Genera un informe técnico sobre el impacto ambiental que causan las operaciones durante cada fase. Dichas fases son: Preparacion, Construccion y Operacion",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_completion_tokens=800,
            temperature=1.0,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            model=deployment
        )

        # Save the generated report
        model_response = response.choices[0].message.content
        models.reports.objects.create(id_project= project, content= model_response)

    # Transform the response into markdown syntax 
    # so it can be displayed properly  
    html_content = markdown2.markdown(
        model_response,
        extras=["fenced-code-blocks", "tables", "cuddled-lists"]
    )

    return render(request, "dashboard/report.html", {'content': html_content})

    