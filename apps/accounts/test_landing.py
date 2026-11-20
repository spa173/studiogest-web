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

    def test_landing_metadata_uses_clean_production_url(self):
        response = self.client.get('/?utm_source=seo')
        origin = 'https://studiogest-web-1.vercel.app'
        self.assertContains(response, f'<link rel="canonical" href="{origin}/">')
        self.assertContains(response, f'<meta property="og:url" content="{origin}/">')
        self.assertContains(response, f'<meta property="og:image" content="{origin}/static/img/landing/social-card.jpg">')
        self.assertContains(response, '<meta name="twitter:card" content="summary_large_image">')

    def test_crawlers_can_discover_the_public_landing(self):
        origin = 'https://studiogest-web-1.vercel.app'
        self.assertContains(self.client.get('/robots.txt'), f'Sitemap: {origin}/sitemap.xml')
        sitemap = self.client.get('/sitemap.xml')
        self.assertContains(sitemap, f'<loc>{origin}/</loc>')
        self.assertNotContains(sitemap, '/accounts/login/')

    def test_login_can_be_crawled_but_should_not_be_indexed(self):
        self.assertContains(
            self.client.get(reverse('accounts:login')),
            '<meta name="robots" content="noindex">',
        )
