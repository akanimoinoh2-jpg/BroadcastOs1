from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import BroadcastSlot, IncidentReport, Notification, Program, Story
from .models import AudioArchive, ImageAsset, VideoAsset, UserProfile

User = get_user_model()


class StoryForm(forms.ModelForm):
    # Optional media uploads - attaching files to a story is never required.
    image = forms.ImageField(required=False, label='Image (optional)',
                             help_text='Photo for this story.')
    image_caption = forms.CharField(max_length=300, required=False, label='Image caption (optional)')
    video = forms.FileField(required=False, label='Video (optional)',
                            help_text='Video clip for this story.')
    video_caption = forms.CharField(max_length=300, required=False, label='Video caption (optional)')
    audio = forms.FileField(required=False, label='Audio (optional)',
                            help_text='Audio clip / voiceover for this story.')
    audio_duration = forms.IntegerField(required=False, min_value=0, label='Audio duration in seconds (optional)')

    class Meta:
        model = Story
        fields = ['title', 'slug', 'body', 'assigned_to', 'status']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Write the full story here...'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            raise forms.ValidationError('A URL-friendly story slug is required.')
        return slug


# Date/time formats accepted by the scheduling forms. The first format is
# what the HTML5 ``datetime-local`` picker submits; the rest let staff type
# common date/time styles manually without hitting "Enter a valid date/time."
DATETIME_INPUT_FORMATS = [
    '%Y-%m-%dT%H:%M',      # HTML5 datetime-local picker value
    '%Y-%m-%dT%H:%M:%S',   # datetime-local with seconds
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %H:%M',
    '%d/%m/%Y %I:%M %p',   # e.g. 28/08/2026 09:00 PM
    '%m/%d/%Y %H:%M:%S',
    '%m/%d/%Y %H:%M',
]


def datetime_picker_widget():
    """HTML5 date+time picker that also renders saved values correctly."""
    return forms.DateTimeInput(
        attrs={'type': 'datetime-local'},
        format='%Y-%m-%dT%H:%M',
    )


class ProgramForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        input_formats=DATETIME_INPUT_FORMATS,
        widget=datetime_picker_widget(),
        help_text='Click the calendar icon and pick the date and time (e.g. 9:00 PM).',
    )
    end_time = forms.DateTimeField(
        input_formats=DATETIME_INPUT_FORMATS,
        widget=datetime_picker_widget(),
        help_text='Click the calendar icon and pick the date and time (e.g. 10:00 PM).',
    )

    class Meta:
        model = Program
        fields = ['title', 'description', 'producer', 'presenter', 'technical_lead', 'studio', 'start_time', 'end_time', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', 'End time must be after the start time.')
        return cleaned_data


class BroadcastSlotForm(forms.ModelForm):
    scheduled_time = forms.DateTimeField(
        input_formats=DATETIME_INPUT_FORMATS,
        widget=datetime_picker_widget(),
        help_text='Click the calendar icon and pick the date and time.',
    )

    class Meta:
        model = BroadcastSlot
        fields = ['program', 'story', 'scheduled_time', 'duration_minutes', 'studio', 'status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = ['title', 'description', 'assigned_to', 'severity', 'status']


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'message', 'recipient', 'level']


class AudioArchiveForm(forms.ModelForm):
    class Meta:
        model = AudioArchive
        fields = ['title', 'description', 'file', 'duration_seconds', 'is_backup_verified', 'story']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ImageAssetForm(forms.ModelForm):
    file = forms.ImageField(required=False)

    class Meta:
        model = ImageAsset
        fields = ['title', 'caption', 'file']


class VideoAssetForm(forms.ModelForm):
    file = forms.FileField(required=False)

    class Meta:
        model = VideoAsset
        fields = ['title', 'caption', 'file']


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            UserProfile.objects.create(user=user, role=self.cleaned_data['role'])
        return user


class AIAssistantForm(forms.Form):
    ACTION_CHOICES = [
        ('summarize', 'Summarize'),
        ('headlines', 'Generate Headlines'),
        ('tags', 'Recommend Tags'),
        ('questions', 'Interview Questions'),
        ('social', 'Social Post'),
        ('outline', 'Script Outline'),
    ]
    text = forms.CharField(widget=forms.Textarea(attrs={'rows':6}), required=True)
    action = forms.ChoiceField(choices=ACTION_CHOICES, required=True)


class ProfileForm(forms.ModelForm):
    """Edit the logged-in user's profile. Profile picture is optional."""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ['role', 'bio', 'phone', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', user.first_name)
        user.last_name = self.cleaned_data.get('last_name', user.last_name)
        user.email = self.cleaned_data.get('email', user.email)
        user.save()
        if commit:
            profile.save()
        return profile
