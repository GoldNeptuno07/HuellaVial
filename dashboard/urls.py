from django.urls import path
from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.main_view, name= "main"),
    path("impact-matrix", views.impact_matrix_view, name= "impact-matrix"),
]