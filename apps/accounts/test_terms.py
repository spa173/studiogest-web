from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(TERMS_VERSION='1.0')
class TermsAcceptanceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='staff', email='staff@example.com', password='test-password',
        )
        self.accept = reverse('accounts:accept_terms')
        self.dashboard = reverse('dashboard:index')

    def test_staff_must_accept_current_terms_before_accessing_dashboard(self):
        response = self.client.post(reverse('accounts:login'), {
            'login': self.user.username, 'password': 'test-password',
        }, follow=True)
        self.assertEqual(response.request['PATH_INFO'], self.accept)
        self.assertRedirects(self.client.get(self.dashboard), f'{self.accept}?next={self.dashboard}')

        for data in ({'version': '1.0'}, {'version': '0.9', 'accepted': 'on'}):
            response = self.client.post(self.accept, data)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(self.user.terms_acceptances.exists())

        response = self.client.post(self.accept, {
            'version': '1.0', 'accepted': 'on',
        })
        self.assertRedirects(response, self.dashboard)
        acceptance = self.user.terms_acceptances.get()
        self.assertEqual(acceptance.version, '1.0')
        self.assertIsNotNone(acceptance.accepted_at)
        self.client.post(self.accept, {'version': '1.0', 'accepted': 'on'})
        self.assertEqual(self.user.terms_acceptances.count(), 1)

        with self.settings(TERMS_VERSION='2.0'):
            self.assertRedirects(self.client.get(self.dashboard), f'{self.accept}?next={self.dashboard}')
            self.client.post(self.accept, {'version': '2.0', 'accepted': 'on'})
        self.assertEqual(set(self.user.terms_acceptances.values_list('version', flat=True)), {'1.0', '2.0'})

    def test_legal_documents_and_reservations_remain_available(self):
        self.client.force_login(self.user)
        for route in ('terms', 'privacy_notice', 'appointments:public_booking'):
            self.assertEqual(self.client.get(reverse(route)).status_code, 200)
        self.assertContains(self.client.get(reverse('terms')), 'envisionone@gmail.com')
        self.assertRedirects(self.client.post(reverse('accounts:logout')), reverse('accounts:login'))

    def test_anonymous_cannot_accept(self):
        response = self.client.post(self.accept, {'version': '1.0', 'accepted': 'on'})
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.accept}")
        self.assertFalse(self.user.terms_acceptances.exists())
