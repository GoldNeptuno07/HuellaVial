from django.urls import path
from . import views

app_name = "dashboard"
urlpatterns = [
    # =======================================
    # HTTP views
    # =======================================
    path("", views.main_view, name= "main"),
    path("<int:project_id>/impact-matrix/<str:phase_name>", views.impact_matrix_view, name= "impact-matrix"),
    # =======================================
    # APIs
    # =======================================
    path("toggle-impact/", views.toggle_impact, name="toggle_impact"),
    path("update_rating/<int:rating_id>/", views.update_rating, name="update_rating"),
    path("add_operation/<int:phase_id>", views.add_operation, name="add_operation"),
    path("update_description/<int:rating_id>", views.update_description, name= "update_description"),
    path("generate_report/<int:project_id>", views.generate_report, name= "generate_report"),
]