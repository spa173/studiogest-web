from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(SESSION_IDLE_SECONDS=1800)
class IdleSessionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='staff', email='staff@example.test', password='test-idle-password',
        )
        self.dashboard_url = reverse('dashboard:index')

    def login_at(self, timestamp):
        with patch('accounts.idle_session.time', return_value=timestamp):
            return self.client.post(reverse('accounts:login'), {
                'login': 'staff', 'password': 'test-idle-password', 'remember_me': 'on',
            })

    def test_remember_me_cannot_keep_an_idle_session_open(self):
        self.assertRedirects(self.login_at(1000), self.dashboard_url, fetch_redirect_response=False)
        with patch('accounts.idle_session.time', return_value=2800):
            response = self.client.get(self.dashboard_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.dashboard_url}",
                             fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_status_reads_do_not_extend_session_but_activity_does(self):
        self.login_at(1000)
        url = reverse('accounts:session_activity')
        with patch('accounts.idle_session.time', return_value=1500):
            self.assertEqual(self.client.get(url).json()['remaining_seconds'], 1300)
        with patch('accounts.idle_session.time', return_value=2000):
            self.assertEqual(self.client.post(url).json()['remaining_seconds'], 1800)
        with patch('accounts.idle_session.time', return_value=2800):
            self.assertEqual(self.client.get(url).json()['remaining_seconds'], 1000)
        with patch('accounts.idle_session.time', return_value=3800):
            self.assertEqual(self.client.post(url).status_code, 401)
