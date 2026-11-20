from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class LandingPageTests(TestCase):
    def test_public_home_links_to_real_studiogest_flows(self):
        response = self.client.get(reverse('root'))
        self.assertTemplateUsed(response, 'landing.html')
        for name in ('accounts:login', 'appointments:public_booking', 'privacy_notice', 'terms'):
            self.assertContains(response, f'href="{reverse(name)}"')

    def test_signed_in_staff_keep_dashboard_as_home(self):
        user = get_user_model().objects.create_user(username='staff', email='staff@example.com')
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse('root')), reverse('dashboard:index'))
