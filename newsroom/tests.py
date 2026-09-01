from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .forms import ImageAssetForm, VideoAssetForm
from .models import ImageAsset, Story, UserProfile

User = get_user_model()


class AuthFlowTests(TestCase):
    def test_user_can_register_and_be_logged_in(self):
        response = self.client.post(
            reverse('newsroom:register'),
            {
                'username': 'reporter1',
                'first_name': 'Amina',
                'last_name': 'Khan',
                'email': 'amina@example.com',
                'role': 'reporter',
                'password1': 'SecurePass123!',
                'password2': 'SecurePass123!',
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='reporter1')
        self.assertTrue(user.check_password('SecurePass123!'))
        self.assertTrue(UserProfile.objects.filter(user=user, role='reporter').exists())
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_user_can_log_in_with_email(self):
        user = User.objects.create_user(
            username='producer_test',
            email='producer@example.com',
            password='SecurePass123!',
        )
        UserProfile.objects.create(user=user, role='producer')

        self.assertTrue(self.client.login(username='producer@example.com', password='SecurePass123!'))

    def test_home_redirects_logged_in_users_to_dashboard(self):
        user = User.objects.create_user(
            username='dashboard_user',
            email='dashboard@example.com',
            password='SecurePass123!',
        )
        self.client.login(username='dashboard_user', password='SecurePass123!')

        response = self.client.get(reverse('newsroom:home'))
        self.assertRedirects(response, reverse('newsroom:dashboard'))

    def test_dashboard_shows_story_media_when_present(self):
        user = User.objects.create_user(
            username='editor_test',
            email='editor@example.com',
            password='SecurePass123!',
        )
        self.client.login(username='editor_test', password='SecurePass123!')

        story = Story.objects.create(
            title='Election Coverage',
            slug='election-coverage',
            body='This is a sample story body for media coverage.',
            created_by=user,
            assigned_to=user,
            status='published',
        )
        ImageAsset.objects.create(
            story=story,
            title='Cover image',
            caption='Election crowd',
            file=SimpleUploadedFile('cover.jpg', b'fakeimage', content_type='image/jpeg'),
        )

        response = self.client.get(reverse('newsroom:dashboard'))
        self.assertContains(response, 'Election Coverage')
        self.assertContains(response, 'Election crowd')
        self.assertContains(response, '/media/images/')

    def test_story_media_uploads_are_optional(self):
        user = User.objects.create_user(username='editor', email='editor@example.com', password='SecurePass123!')
        story = Story.objects.create(
            title='Optional media story',
            slug='optional-media-story',
            body='This story has no photo or video attached yet.',
            created_by=user,
            status='draft',
        )

        self.assertTrue(ImageAssetForm(data={'title': 'Image draft', 'caption': 'No file attached'}).is_valid())
        self.assertTrue(VideoAssetForm(data={'title': 'Video draft', 'caption': 'No file attached'}).is_valid())

        self.client.force_login(user)
        response = self.client.post(reverse('newsroom:image_upload', args=[story.slug]), {'title': 'No upload', 'caption': 'Optional'})
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('newsroom:video_upload', args=[story.slug]), {'title': 'No upload', 'caption': 'Optional'})
        self.assertEqual(response.status_code, 302)

    def test_ai_assistant_handles_submit_and_invalid_form(self):
        user = User.objects.create_user(username='ai_user', email='ai_user@example.com', password='SecurePass123!')
        self.client.force_login(user)

        response = self.client.post(
            reverse('newsroom:ai_assistant'),
            {'text': 'Breaking news from our station. The team reported several updates today.', 'action': 'summarize'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Breaking news')

        invalid = self.client.post(reverse('newsroom:ai_assistant'), {'text': '', 'action': 'summarize'})
        self.assertEqual(invalid.status_code, 200)
        self.assertContains(invalid, 'AI Assistant')
