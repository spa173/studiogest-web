from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import DemoRequest

SUCCESS = 'Recibimos tu solicitud de demostración.'


class DemoRequestTests(TestCase):
    def setUp(self):
        self.url = reverse('demo_request')
        self.data = {
            'request_id': str(uuid4()),
            'name': 'Ana Demo',
            'business_name': 'Salón Prisma',
            'email': 'ana@example.test',
            'phone': '3005550101',
            'message': 'Quiero conocer la agenda.',
            'contact_consent': 'on',
            'website': '',
        }

    def test_public_submission_saves_once_and_displays_confirmation(self):
        self.assertContains(self.client.get(reverse('root')), f'action="{self.url}#demo"')
        for _ in range(2):
            response = self.client.post(self.url, self.data, follow=True)
            self.assertContains(response, SUCCESS)
        self.assertEqual(DemoRequest.objects.count(), 1)
        saved = DemoRequest.objects.get()
        self.assertEqual(saved.email, self.data['email'])
        self.assertTrue(saved.contact_consent)
        self.assertIsNotNone(saved.created_at)
        self.assertNotContains(self.client.get(reverse('root')), SUCCESS)

    def test_invalid_email_or_missing_consent_does_not_save(self):
        response = self.client.post(self.url, {**self.data, 'email': 'incorrect', 'contact_consent': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['demo_form'].has_error('email', 'invalid'))
        self.assertTrue(response.context['demo_form'].has_error('contact_consent', 'required'))
        self.assertFalse(DemoRequest.objects.exists())

    def test_post_requires_csrf_and_honeypot_ignores_bots(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.url, self.data).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertContains(self.client.post(self.url, {**self.data, 'website': 'spam'}, follow=True), SUCCESS)
        self.assertFalse(DemoRequest.objects.exists())

    def test_only_the_platform_superuser_can_read_requests_in_admin(self):
        self.client.post(self.url, self.data)
        users = get_user_model()
        ordinary = users.objects.create_user(username='admin', email='admin@example.test', role='ADMIN', is_staff=True, password='test-password')
        root = users.objects.create_superuser(username='root', email='root@example.test', password='test-password')
        url = reverse('admin:dashboard_demorequest_changelist')
        self.client.post(reverse('admin:login'), {'username': ordinary.username, 'password': 'test-password'})
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.post(reverse('admin:login'), {'username': root.username, 'password': 'test-password'})
        self.assertContains(self.client.get(url), 'ana@example.test')
