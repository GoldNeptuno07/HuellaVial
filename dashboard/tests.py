from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from . import models

# Create your tests here.
class ProjectsModelTests(TestCase):
    def test_was_displayed_recently_with_future_project(self):
        """
            Assess function to get the projects with a creation date
            between "now - 16 days <= creation_date <= now"
        """
        future_project = models.projects(creation_date=timezone.now() + timedelta(days=30))
        self.assertIs(future_project.was_published_recently(), False)
    
class DashboardViewTests(TestCase):
    def test_main_view_with_no_projects(self):
        """
            If no projects exist, an appropriate message should be displayed.
        """
        response = self.client.get(reverse("dashboard:main"))
        self.assertEqual(response.status_code, 200)

    def test_main_view_display_available_projects(self):
        """
            Test to assess that the available projects are being displayed. 
        """
        # Project with recent date
        recent_project1 = models.projects.objects.create(name="Recent Project")
        recent_project2 = models.projects.objects.create(name="Recent Project")

        response = self.client.get(reverse("dashboard:main"))
        self.assertQuerySetEqual(response.context['recent_projects'], [recent_project1,recent_project2])