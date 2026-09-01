from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from .services import (
    generate_ai_headlines,
    generate_interview_questions,
    generate_social_post,
    generate_script_outline,
    recommend_tags,
    summarize_text,
)

User = get_user_model()


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('station_manager', 'Station Manager'),
        ('editor', 'Editor'),
        ('producer', 'Producer'),
        ('presenter', 'Presenter'),
        ('reporter', 'Reporter'),
        ('technician', 'Technician / Audio Engineer'),
        ('administrator', 'Administrator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"


class Studio(models.Model):
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=180, blank=True)
    is_active = models.BooleanField(default=True)
    capacity = models.PositiveIntegerField(default=4)

    def __str__(self):
        return self.name


class Program(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('on_air', 'On Air'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    producer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='produced_programs',
    )
    presenter = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='presented_programs',
    )
    technical_lead = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='technical_programs',
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    studio = models.ForeignKey(
        Studio,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='programs',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    schedule_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def is_live(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time


class Story(models.Model):
    STATUS_CHOICES = [
        ('idea', 'Idea'),
        ('assigned', 'Assigned'),
        ('writing', 'Writing'),
        ('editing', 'Editing'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True)
    summary = models.TextField(blank=True)
    body = models.TextField()
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='stories_created',
    )
    assigned_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='stories_assigned',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idea')
    suggested_tags = models.JSONField(default=list, blank=True)
    headline_suggestions = models.JSONField(default=list, blank=True)
    story_outline = models.JSONField(default=list, blank=True)
    interview_questions = models.JSONField(default=list, blank=True)
    social_post = models.TextField(blank=True)
    ai_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.summary and self.body:
            self.summary = summarize_text(self.body)
        if self.body and not self.headline_suggestions:
            self.headline_suggestions = generate_ai_headlines(self.body)
        if self.body and not self.suggested_tags:
            self.suggested_tags = recommend_tags(self.body)
        super().save(*args, **kwargs)

    def generate_ai_summary(self):
        self.summary = summarize_text(self.body)
        self.ai_notes = 'AI summary generated from the latest story body.'
        self.save(update_fields=['summary', 'ai_notes', 'updated_at'])
        return self.summary

    def generate_ai_headlines(self):
        self.headline_suggestions = generate_ai_headlines(self.body)
        self.ai_notes = 'AI headline suggestions refreshed.'
        self.save(update_fields=['headline_suggestions', 'ai_notes', 'updated_at'])
        return self.headline_suggestions

    def refresh_tags(self):
        self.suggested_tags = recommend_tags(self.body)
        self.ai_notes = 'AI tags recommended for this story.'
        self.save(update_fields=['suggested_tags', 'ai_notes', 'updated_at'])
        return self.suggested_tags

    def generate_script_outline(self):
        self.story_outline = generate_script_outline(self.body)
        self.ai_notes = 'AI script outline generated.'
        self.save(update_fields=['story_outline', 'ai_notes', 'updated_at'])
        return self.story_outline

    def generate_interview_questions(self):
        self.interview_questions = generate_interview_questions(self.body)
        self.ai_notes = 'AI interview questions generated.'
        self.save(update_fields=['interview_questions', 'ai_notes', 'updated_at'])
        return self.interview_questions

    def generate_social_post(self):
        self.social_post = generate_social_post(self.body)
        self.ai_notes = 'AI social media content generated.'
        self.save(update_fields=['social_post', 'ai_notes', 'updated_at'])
        return self.social_post


class BroadcastSlot(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ready', 'Ready'),
        ('live', 'Live'),
        ('completed', 'Completed'),
    ]

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='broadcast_slots',
    )
    story = models.ForeignKey(
        Story,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='broadcast_slots',
    )
    scheduled_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=15)
    studio = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_time']

    def __str__(self):
        return f"{self.program.title} @ {self.scheduled_time:%Y-%m-%d %H:%M}"

    @property
    def is_upcoming(self):
        return self.scheduled_time > timezone.now()

    @property
    def is_live(self):
        return self.status == 'live'


class BroadcastLog(models.Model):
    EVENT_CHOICES = [
        ('script_approved', 'Script Approved'),
        ('on_air', 'On Air'),
        ('technical_check', 'Technical Check'),
        ('archive_published', 'Archive Published'),
    ]

    program = models.ForeignKey(
        Program,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='broadcast_logs',
    )
    event_time = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=60, choices=EVENT_CHOICES)
    message = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='broadcast_logs',
    )

    def __str__(self):
        return f"{self.event_type} at {self.event_time:%Y-%m-%d %H:%M}"


class IncidentReport(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=220)
    description = models.TextField()
    reported_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='incidents_reported',
    )
    assigned_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='incidents_assigned',
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='low')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.get_severity_display()})"

    def mark_resolved(self):
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save(update_fields=['status', 'resolved_at', 'updated_at'])


class Notification(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('alert', 'Alert'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    recipient = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.get_level_display()}"


class AudioArchive(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    story = models.ForeignKey(
        Story,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audio_archives',
    )
    file = models.FileField(upload_to='audio_archives/', blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    archived_at = models.DateTimeField(auto_now_add=True)
    is_backup_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class ImageAsset(models.Model):
    title = models.CharField(max_length=200, blank=True)
    caption = models.CharField(max_length=300, blank=True)
    story = models.ForeignKey(
        Story,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='images',
    )
    file = models.ImageField(upload_to='images/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='uploaded_images',
    )

    def __str__(self):
        return self.title or (self.file.name if self.file else 'Image')


class VideoAsset(models.Model):
    title = models.CharField(max_length=200, blank=True)
    caption = models.CharField(max_length=300, blank=True)
    story = models.ForeignKey(
        Story,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='videos',
    )
    file = models.FileField(upload_to='videos/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='uploaded_videos',
    )

    def __str__(self):
        return self.title or (self.file.name if self.file else 'Video')
