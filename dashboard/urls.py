from django.urls import path
from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.main_view, name= "main"),
    path("<int:project_id>/impact-matrix/<str:phase_name>", views.impact_matrix_view, name= "impact-matrix"),
]