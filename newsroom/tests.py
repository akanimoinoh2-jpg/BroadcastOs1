from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .forms import ImageAssetForm, VideoAssetForm
from .models import ImageAsset, Story, UserProfile

User = get_user_model()


class AuthFlowTests(TestCase):
    def test_home_redirects_to_dashboard(self):
        response = self.client.get(reverse('newsroom:home'))
        self.assertRedirects(response, reverse('newsroom:dashboard'))

    def test_dashboard_shows_story_media_when_present(self):
        user = User.objects.create_user(
            username='editor_test',
            email='editor@example.com',
            password='SecurePass123!',
        )

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

        response = self.client.post(reverse('newsroom:image_upload', args=[story.slug]), {'title': 'No upload', 'caption': 'Optional'})
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('newsroom:video_upload', args=[story.slug]), {'title': 'No upload', 'caption': 'Optional'})
        self.assertEqual(response.status_code, 302)

    def test_ai_assistant_handles_submit_and_invalid_form(self):
        response = self.client.post(
            reverse('newsroom:ai_assistant'),
            {'text': 'Breaking news from our station. The team reported several updates today.', 'action': 'summarize'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Breaking news')

        invalid = self.client.post(reverse('newsroom:ai_assistant'), {'text': '', 'action': 'summarize'})
        self.assertEqual(invalid.status_code, 200)
        self.assertContains(invalid, 'AI Assistant')
