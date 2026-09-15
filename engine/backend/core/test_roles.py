from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from core.models import Usuario

class RolesSecurityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create_user(email="admin@test.com", password="pwd", rol="ADMIN", nombre="Ad", apellido="A", is_staff=True, is_superuser=True)
        self.profesor = Usuario.objects.create_user(email="prof@test.com", password="pwd", rol="PROFESOR", nombre="Pr", apellido="P")
        self.alumna = Usuario.objects.create_user(email="alum@test.com", password="pwd", rol="CLIENTE", nombre="Al", apellido="A")

    def test_admin_access(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/alumnos/')
        self.assertEqual(response.status_code, 200)

    def test_profesor_access_denied_to_admin(self):
        self.client.force_authenticate(user=self.profesor)
        response = self.client.get('/api/admin/alumnos/')
        # Should be forbidden or unauthorized because IsAdminUser is required
        self.assertEqual(response.status_code, 403)

    def test_alumna_access_denied_to_admin(self):
        self.client.force_authenticate(user=self.alumna)
        response = self.client.get('/api/admin/alumnos/')
        self.assertEqual(response.status_code, 403)
        
    def test_unauthenticated_access_denied(self):
        response = self.client.get('/api/admin/alumnos/')
        self.assertEqual(response.status_code, 401)
