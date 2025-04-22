from django.urls import path
from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.main_view, name= "main"),
    path("<int:project_id>/impact-matrix/<str:phase_name>", views.impact_matrix_view, name= "impact-matrix"),
    path("toggle-impact/", views.toggle_impact, name="toggle_impact"),
    path("update_rating/<int:rating_id>/", views.update_rating, name="update_rating"),
    path("add_operation/<int:phase_id>", views.add_operation, name="add_operation"),
]