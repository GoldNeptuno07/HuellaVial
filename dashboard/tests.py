from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from . import models

# Create your tests here.
class ProjectsModelTests(TestCase):
    def test_was_displayed_recently_with_future_project(self):
        """
            was_displayed_recently() returns False for projects whose
            creation_date is in the future.
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

    def test_main_view_with_no_future_projects(self):
        """
            It does not display future projects.
        """
        future_project = models.projects.objects.create(name="Future Project", creation_date=timezone.now() + timedelta(days=30))
        response = self.client.get(reverse("dashboard:main"))
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['recent_projects'], [])
        self.assertQuerySetEqual(response.context['old_projects'], [])

    def test_main_view_display_available_projects(self):
        """
            If projects exist, they should be displayed.
        """
        recent_project = models.projects.objects.create(name="Recent Project", creation_date=timezone.now())
        time = timezone.now() - timedelta(days=60)
        old_project = models.projects.objects.create(name="Past Project", creation_date= time)

        response = self.client.get(reverse("dashboard:main"))
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['recent_projects'], [recent_project])
        self.assertQuerySetEqual(response.context['old_projects'], [old_project])