from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


class RootSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='root', email='root@example.com', password='Test-only-password-42',
        )
        self.client.force_login(self.user)

    @override_settings(ADMIN_ACCESS_ALERT_EMAIL='security@example.com',
                       EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_first_admin_entry_is_reported_once_in_the_session(self):
        for _ in range(2):
            self.assertEqual(self.client.get(reverse('admin:index'), REMOTE_ADDR='192.0.2.10',
                                             HTTP_USER_AGENT='Test browser').status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('192.0.2.10', mail.outbox[0].body)
        self.assertIn('Test browser', mail.outbox[0].body)

    def test_root_can_open_enrollment(self):
        response = self.client.get(reverse('accounts:mfa_setup'))
        self.assertContains(response, 'Activar multifactor')
        self.assertIn('no-store', response['Cache-Control'])

    def test_email_login_works_in_both_panels(self):
        self.client.logout()
        response = self.client.post(reverse('admin:login'), {
            'username': 'ROOT@example.com', 'password': 'Test-only-password-42',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))
        self.client.logout()
        response = self.client.post(reverse('accounts:login'), {
            'login': 'ROOT@example.com', 'password': 'Test-only-password-42',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.pk))

    def test_enrollment_blocks_both_panels_and_recovery_code_is_single_use(self):
        from django_otp.oath import TOTP

        setup = reverse('accounts:mfa_setup')
        verify = reverse('accounts:mfa_verify')
        self.assertNotContains(self.client.get(setup), 'Clave de configuración manual')
        self.assertRedirects(self.client.post(setup, {'password': 'Test-only-password-42'}), setup)
        self.assertContains(self.client.get(setup), 'Clave de configuración manual')
        key = bytes.fromhex(self.client.session['privileged_mfa_setup']['key'])
        token = f'{TOTP(key).token():06d}'
        enrollment = self.client.post(setup, {'token': token})
        self.assertContains(enrollment, 'Multifactor activado')
        recovery_code = enrollment.context['recovery_codes'][0]
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)

        self.client.logout()
        self.client.force_login(self.user)
        for panel in ('admin:index', 'dashboard:index'):
            response = self.client.get(reverse(panel))
            self.assertRedirects(response, f'{verify}?next={reverse(panel)}', fetch_redirect_response=False)
        self.assertContains(self.client.post(verify, {'token': token}), 'Código incorrecto')
        from django_otp.plugins.otp_totp.models import TOTPDevice
        TOTPDevice.objects.get(user=self.user).throttle_reset()

        self.assertRedirects(self.client.post(verify, {'token': recovery_code}), reverse('dashboard:index'))
        self.client.logout()
        self.client.force_login(self.user)
        self.assertContains(self.client.post(verify, {'token': recovery_code}), 'Código incorrecto')
