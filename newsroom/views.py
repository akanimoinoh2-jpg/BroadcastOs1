from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse

from .forms import (
    BroadcastSlotForm,
    IncidentReportForm,
    NotificationForm,
    ProgramForm,
    RegistrationForm,
    StoryForm,
)
from .models import (
    AudioArchive,
    BroadcastLog,
    BroadcastSlot,
    ImageAsset,
    IncidentReport,
    Notification,
    Program,
    Story,
    UserProfile,
    VideoAsset,
)

from .models import Studio
from .forms import AudioArchiveForm, ImageAssetForm, VideoAssetForm
from .forms import AIAssistantForm, ProfileForm
from .services import (
    summarize_text,
    generate_ai_headlines,
    recommend_tags,
    generate_interview_questions,
    generate_social_post,
    generate_script_outline,
)

User = get_user_model()


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            authenticated_user = authenticate(
                request,
                username=user.username,
                password=form.cleaned_data['password1'],
            )
            if authenticated_user is not None:
                login(request, authenticated_user)
                messages.success(request, 'Account created successfully. Welcome to BroadcastOS.')
                return redirect('newsroom:dashboard')
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('newsroom:profile')
    else:
        form = ProfileForm(instance=profile_obj)
    return render(request, 'newsroom/profile.html', {'form': form, 'profile_obj': profile_obj})


def home(request):
    if request.user.is_authenticated:
        return redirect('newsroom:dashboard')
    return redirect('login')


@login_required
def dashboard(request):
    stories = Story.objects.prefetch_related('images', 'videos').order_by('-updated_at')[:6]
    programs = Program.objects.filter(status__in=['scheduled', 'on_air']).order_by('start_time')[:5]
    # Use current time for upcoming slots; avoid passing None into queryset filters
    upcoming_slots = BroadcastSlot.objects.filter(scheduled_time__gte=timezone.now()).order_by('scheduled_time')[:5]
    incident_count = IncidentReport.objects.filter(status__in=['open', 'investigating']).count()
    notifications = Notification.objects.filter(is_read=False).order_by('-created_at')[:5]

    return render(request, 'newsroom/dashboard.html', {
        'stories': stories,
        'programs': programs,
        'upcoming_slots': upcoming_slots,
        'incident_count': incident_count,
        'notifications': notifications,
    })


@login_required
def system_overview(request):
    # ---- Users & Roles ----
    role_data = dict(UserProfile.objects.values_list('role').annotate(count=Count('id')))
    role_colors = {
        'station_manager': '#4a90d9',
        'editor': '#d9a24a',
        'producer': '#9b6fd4',
        'presenter': '#d96a9b',
        'reporter': '#5fd47a',
        'technician': '#d4c94a',
        'administrator': '#d96a6a',
    }
    roles = []
    for value, label in UserProfile.ROLE_CHOICES:
        roles.append({
            'label': label,
            'count': role_data.get(value, 0),
            'initial': label.split()[0][0],
            'color': role_colors.get(value, '#4a90d9'),
        })

    # ---- Access Layer ----
    access_layer = [
        {'title': 'Responsive Web App', 'description': 'Access the full BroadcastOS platform from any device, anywhere.'},
        {'title': 'Mobile Friendly UI', 'description': 'Optimised interface for reporters and production crews in the field.'},
        {'title': 'Encrypted Login & Role-Based Access', 'description': 'Secure authentication with role-based permissions for every team member.'},
    ]

    # ---- Platform Modules ----
    module_color = '#9b6fd4'
    module_bg = 'rgba(155,111,212,0.16)'

    def _m(name, icon, url, description):
        return {
            'name': name,
            'icon': icon,
            'url': url,
            'description': description,
            'color': module_color,
            'bg': module_bg,
        }

    modules = [
        _m('Dashboard', '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>', reverse('newsroom:dashboard'), 'Overview of newsroom operations, schedule, alerts and AI workflows.'),
        _m('Newsroom', '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8M16 17H8M10 9H8"/>', reverse('newsroom:story_list'), 'Manage story ideas, coverage and editorial content.'),
        _m('Programme Scheduling', '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>', reverse('newsroom:program_list'), 'Plan and schedule programmes, presenters and studios.'),
        _m('Reporter Management', '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>', reverse('newsroom:reporter_list'), 'Assign reporters to stories and manage coverage.'),
        _m('Presenter Management', '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><path d="M12 19v3"/>', reverse('newsroom:presenter_list'), 'Manage presenters and programme hosts.'),
        _m('Editorial Workflow', '<circle cx="5" cy="6" r="3"/><circle cx="19" cy="6" r="3"/><circle cx="12" cy="18" r="3"/><path d="M7 7h10M7 7l4 8M17 7l-4 8"/>', reverse('newsroom:story_list'), 'Track stories through the full editorial pipeline.'),
        _m('Technical Operations', '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>', reverse('newsroom:technical_list'), 'Manage studios, technical leads and broadcast equipment.'),
        _m('Live Broadcast Control', '<circle cx="12" cy="12" r="3"/><path d="M5 12a7 7 0 0 1 14 0"/><path d="M2 12a10 10 0 0 1 20 0"/>', reverse('newsroom:live_control'), 'Control live broadcast slots and on-air status.'),
        _m('Audio Management', '<path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M19 5a9 9 0 0 1 0 14"/>', reverse('newsroom:audio_list'), 'Archive, store and verify audio assets and backups.'),
        _m('AI Assistant', '<path d="M12 2l1.9 5.8L20 9.7l-6.1 1.9L12 17l-1.9-5.4L4 9.7l6.1-1.9L12 2z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"/>', reverse('newsroom:ai_assistant'), 'AI news writer, headlines, scripts, summaries and social posts.'),
        _m('Reports', '<path d="M18 20V10M12 20V4M6 20v-6"/>', reverse('newsroom:reports'), 'Generate and export operational reports.'),
        _m('Administration', '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.8-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.8 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.8.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.8V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>', '/admin/', 'System administration and user management.'),
        _m('Incident Register', '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4M12 17h.01"/>', reverse('newsroom:incident_list'), 'Log and track technical and operational incidents.'),
        _m('Notifications', '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>', reverse('newsroom:notification_list'), 'Broadcast alerts and notifications across the newsroom.'),
        _m('Analytics', '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>', reverse('newsroom:analytics'), 'Track performance, engagement and operational metrics.'),
    ]

    # ---- Workflow ----
    story_status_counts = dict(Story.objects.values_list('status').annotate(count=Count('id')))
    workflow_colors = ['#e87373', '#d05858', '#c24545', '#b83b3b', '#d96a6a', '#e08585', '#c95555', '#b04040']
    workflow_defs = [
        ('Story Idea', 'A story idea is pitched and logged into the newsroom.', 'idea'),
        ('Editor Assigns', 'The editor assigns a reporter and deadline.', 'assigned'),
        ('Reporter Covers', 'The reporter researches, gathers and writes the story.', 'writing'),
        ('Script Approval', 'The editor reviews and approves the script.', 'editing'),
        ('Producer Confirms', 'The producer signs off for broadcast.', 'approved'),
        ('On Air', 'The story goes live on air.', 'published'),
        ('Log Generated', 'A broadcast log is generated automatically.', None),
        ('Archive & Report', 'The story is archived and a report is generated.', 'archived'),
    ]
    log_count = BroadcastLog.objects.count()
    workflow_stages = []
    for idx, (label, description, status_key) in enumerate(workflow_defs):
        count = log_count if status_key is None else story_status_counts.get(status_key, 0)
        workflow_stages.append({
            'label': label,
            'description': description,
            'count': count,
            'color': workflow_colors[idx],
        })

    # ---- AI Services ----
    ai_services = [
        {'title': 'AI News Writer', 'items': ['Headlines', 'Scripts', 'Interview Questions']},
        {'title': 'Research & Distribution', 'items': ['Research', 'Summary', 'Translation', 'Social Media Generator']},
    ]

    # ---- Data & Platform Services ----
    icon_people = '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
    icon_doc = '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>'
    icon_cal = '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>'
    icon_clock = '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>'
    icon_alert = '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4M12 17h.01"/>'
    icon_audio = '<path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/>'
    data_services = [
        {'label': 'Users', 'count': User.objects.count(), 'icon': icon_people},
        {'label': 'Stories', 'count': Story.objects.count(), 'icon': icon_doc},
        {'label': 'Programmes', 'count': Program.objects.count(), 'icon': icon_cal},
        {'label': 'Broadcast Slots', 'count': BroadcastSlot.objects.count(), 'icon': icon_clock},
        {'label': 'Incidents', 'count': IncidentReport.objects.count(), 'icon': icon_alert},
        {'label': 'Audio Archives', 'count': AudioArchive.objects.count(), 'icon': icon_audio},
    ]
    backup_verified = AudioArchive.objects.filter(is_backup_verified=True).count()
    audio_archives_count = AudioArchive.objects.count()

    return render(request, 'newsroom/system_overview.html', {
        'roles': roles,
        'access_layer': access_layer,
        'modules': modules,
        'workflow_stages': workflow_stages,
        'ai_services': ai_services,
        'data_services': data_services,
        'backup_verified': backup_verified,
        'audio_archives_count': audio_archives_count,
    })


@login_required
def reporter_list(request):
    reporters = User.objects.filter(userprofile__role='reporter').order_by('username')
    data = []
    for rep in reporters:
        assigned = Story.objects.filter(assigned_to=rep)
        data.append({
            'user': rep,
            'full_name': rep.get_full_name() or rep.username,
            'story_count': assigned.count(),
            'active_count': assigned.filter(status__in=['assigned', 'writing', 'editing']).count(),
        })
    return render(request, 'newsroom/reporter_list.html', {'reporters': data})


@login_required
def presenter_list(request):
    presenters = User.objects.filter(userprofile__role='presenter').order_by('username')
    data = []
    for pres in presenters:
        programs = Program.objects.filter(presenter=pres)
        data.append({
            'user': pres,
            'full_name': pres.get_full_name() or pres.username,
            'program_count': programs.count(),
            'upcoming_count': programs.filter(status__in=['scheduled', 'on_air']).count(),
        })
    return render(request, 'newsroom/presenter_list.html', {'presenters': data})


@login_required
def technical_list(request):
    studios = Studio.objects.all()
    technical_programs = Program.objects.filter(technical_lead__isnull=False).select_related('technical_lead').order_by('-start_time')[:10]
    return render(request, 'newsroom/technical_list.html', {'studios': studios, 'technical_programs': technical_programs})


@login_required
def live_control(request):
    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        new_status = request.POST.get('status')
        valid_statuses = dict(BroadcastSlot.STATUS_CHOICES)
        if slot_id and new_status in valid_statuses:
            slot = get_object_or_404(BroadcastSlot, pk=slot_id)
            slot.status = new_status
            slot.save()
            messages.success(request, f"Slot status updated to {slot.get_status_display()}.")
            return redirect('newsroom:live_control')
    slots = BroadcastSlot.objects.select_related('program', 'story').order_by('scheduled_time')
    return render(request, 'newsroom/live_control.html', {'slots': slots, 'status_choices': BroadcastSlot.STATUS_CHOICES})


@login_required
def reports(request):
    story_status = Story.objects.values('status').annotate(count=Count('id')).order_by('status')
    program_status = Program.objects.values('status').annotate(count=Count('id')).order_by('status')
    incident_status = IncidentReport.objects.values('status').annotate(count=Count('id')).order_by('status')
    slot_status = BroadcastSlot.objects.values('status').annotate(count=Count('id')).order_by('status')
    return render(request, 'newsroom/reports.html', {
        'story_status': story_status,
        'program_status': program_status,
        'incident_status': incident_status,
        'slot_status': slot_status,
        'total_stories': Story.objects.count(),
        'total_programs': Program.objects.count(),
        'total_incidents': IncidentReport.objects.count(),
        'total_slots': BroadcastSlot.objects.count(),
    })


@login_required
def analytics(request):
    story_by_status = list(Story.objects.values('status').annotate(count=Count('id')).order_by('status'))
    program_by_status = list(Program.objects.values('status').annotate(count=Count('id')).order_by('status'))
    incident_by_severity = list(IncidentReport.objects.values('severity').annotate(count=Count('id')).order_by('severity'))
    story_counts = [s['count'] for s in story_by_status] or [1]
    program_counts = [p['count'] for p in program_by_status] or [1]
    incident_counts = [i['count'] for i in incident_by_severity] or [1]
    max_story = max(story_counts)
    max_program = max(program_counts)
    max_incident = max(incident_counts)

    def _add_width(rows, max_count):
        for row in rows:
            row['width'] = round((row['count'] / max_count) * 100) if max_count else 0
        return rows

    story_by_status = _add_width(story_by_status, max_story)
    program_by_status = _add_width(program_by_status, max_program)
    incident_by_severity = _add_width(incident_by_severity, max_incident)

    return render(request, 'newsroom/analytics.html', {
        'story_by_status': story_by_status,
        'program_by_status': program_by_status,
        'incident_by_severity': incident_by_severity,
    })


@login_required
def story_list(request):
    stories = Story.objects.order_by('-published_at', '-updated_at')
    return render(request, 'newsroom/story_list.html', {'stories': stories})


@login_required
def story_detail(request, slug):
    story = get_object_or_404(Story, slug=slug)
    image_form = ImageAssetForm()
    video_form = VideoAssetForm()
    images = story.images.order_by('-uploaded_at') if hasattr(story, 'images') else []
    videos = story.videos.order_by('-uploaded_at') if hasattr(story, 'videos') else []
    return render(request, 'newsroom/story_detail.html', {
        'story': story,
        'image_form': image_form,
        'video_form': video_form,
        'images': images,
        'videos': videos,
    })


@login_required
def image_upload(request, slug):
    story = get_object_or_404(Story, slug=slug)
    if request.method == 'POST':
        form = ImageAssetForm(request.POST, request.FILES)
        if form.is_valid() and request.FILES.get('file'):
            img = form.save(commit=False)
            img.story = story
            img.uploaded_by = request.user
            img.save()
    return redirect(reverse('newsroom:story_detail', args=[story.slug]))


@login_required
def video_upload(request, slug):
    story = get_object_or_404(Story, slug=slug)
    if request.method == 'POST':
        form = VideoAssetForm(request.POST, request.FILES)
        if form.is_valid() and request.FILES.get('file'):
            vid = form.save(commit=False)
            vid.story = story
            vid.uploaded_by = request.user
            vid.save()
    return redirect(reverse('newsroom:story_detail', args=[story.slug]))


def _save_story_media(story, form, user):
    """Attach optional image/video/audio uploads from the story form."""
    cd = form.cleaned_data
    if cd.get('image'):
        ImageAsset.objects.create(
            story=story, file=cd['image'], title=cd.get('image_caption') or story.title,
            caption=cd.get('image_caption') or '', uploaded_by=user,
        )
    if cd.get('video'):
        VideoAsset.objects.create(
            story=story, file=cd['video'], title=cd.get('video_caption') or story.title,
            caption=cd.get('video_caption') or '', uploaded_by=user,
        )
    if cd.get('audio'):
        AudioArchive.objects.create(
            story=story, file=cd['audio'], title=story.title,
            duration_seconds=cd.get('audio_duration') or 0,
        )


@login_required
def story_create(request):
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.created_by = request.user
            story.save()
            _save_story_media(story, form, request.user)
            return redirect(reverse('newsroom:story_detail', args=[story.slug]))
    else:
        form = StoryForm()
    return render(request, 'newsroom/story_form.html', {'form': form})


@login_required
def story_edit(request, slug):
    story = get_object_or_404(Story, slug=slug)
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES, instance=story)
        if form.is_valid():
            form.save()
            _save_story_media(story, form, request.user)
            return redirect(reverse('newsroom:story_detail', args=[story.slug]))
    else:
        form = StoryForm(instance=story)
    return render(request, 'newsroom/story_form.html', {'form': form, 'story': story})


@login_required
def story_generate_ai(request, slug):
    story = get_object_or_404(Story, slug=slug)
    story.generate_ai_summary()
    story.generate_ai_headlines()
    story.refresh_tags()
    story.generate_script_outline()
    story.generate_interview_questions()
    story.generate_social_post()
    return redirect(reverse('newsroom:story_detail', args=[story.slug]))


@login_required
def program_list(request):
    programs = Program.objects.order_by('-start_time')
    return render(request, 'newsroom/program_list.html', {'programs': programs})


@login_required
def program_create(request):
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('newsroom:program_list'))
    else:
        form = ProgramForm()
    return render(request, 'newsroom/program_form.html', {'form': form})


@login_required
def program_edit(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            return redirect(reverse('newsroom:program_list'))
    else:
        form = ProgramForm(instance=program)
    return render(request, 'newsroom/program_form.html', {'form': form, 'program': program})


@login_required
def slot_list(request):
    slots = BroadcastSlot.objects.order_by('scheduled_time')
    return render(request, 'newsroom/slot_list.html', {'slots': slots})


@login_required
def slot_create(request):
    if request.method == 'POST':
        form = BroadcastSlotForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('newsroom:slot_list'))
    else:
        form = BroadcastSlotForm()
    return render(request, 'newsroom/slot_form.html', {'form': form})


@login_required
def slot_edit(request, pk):
    slot = get_object_or_404(BroadcastSlot, pk=pk)
    if request.method == 'POST':
        form = BroadcastSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return redirect(reverse('newsroom:slot_list'))
    else:
        form = BroadcastSlotForm(instance=slot)
    return render(request, 'newsroom/slot_form.html', {'form': form, 'slot': slot})


@login_required
def incident_list(request):
    incidents = IncidentReport.objects.order_by('-created_at')
    return render(request, 'newsroom/incident_list.html', {'incidents': incidents})


@login_required
def incident_create(request):
    if request.method == 'POST':
        form = IncidentReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reported_by = request.user
            report.save()
            return redirect(reverse('newsroom:incident_list'))
    else:
        form = IncidentReportForm()
    return render(request, 'newsroom/incident_form.html', {'form': form})


@login_required
def incident_edit(request, pk):
    incident = get_object_or_404(IncidentReport, pk=pk)
    if request.method == 'POST':
        form = IncidentReportForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            return redirect(reverse('newsroom:incident_list'))
    else:
        form = IncidentReportForm(instance=incident)
    return render(request, 'newsroom/incident_form.html', {'form': form, 'incident': incident})


@login_required
def notification_list(request):
    notifications = Notification.objects.order_by('-created_at')
    return render(request, 'newsroom/notification_list.html', {'notifications': notifications})


@login_required
def notification_create(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('newsroom:notification_list'))
    else:
        form = NotificationForm()
    return render(request, 'newsroom/notification_form.html', {'form': form})


@login_required
def audio_list(request):
    archives = AudioArchive.objects.order_by('-archived_at')
    return render(request, 'newsroom/audio_list.html', {'archives': archives})


@login_required
def audio_create(request):
    if request.method == 'POST':
        form = AudioArchiveForm(request.POST, request.FILES)
        if form.is_valid():
            archive = form.save()
            return redirect('newsroom:audio_list')
    else:
        form = AudioArchiveForm()
    return render(request, 'newsroom/audio_form.html', {'form': form})


@login_required
def ai_assistant(request):
    result = None
    if request.method == 'POST':
        form = AIAssistantForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            action = form.cleaned_data['action']
            if action == 'summarize':
                result = summarize_text(text)
            elif action == 'headlines':
                result = generate_ai_headlines(text)
            elif action == 'tags':
                result = recommend_tags(text)
            elif action == 'questions':
                result = generate_interview_questions(text)
            elif action == 'social':
                result = generate_social_post(text)
            elif action == 'outline':
                result = generate_script_outline(text)
    else:
        form = AIAssistantForm()
    is_list = isinstance(result, list)
    return render(request, 'newsroom/ai_assistant.html', {'form': form, 'result': result, 'is_list': is_list})
