from django.urls import path

from . import views

app_name = 'newsroom'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('system/', views.system_overview, name='system_overview'),
    path('reporters/', views.reporter_list, name='reporter_list'),
    path('presenters/', views.presenter_list, name='presenter_list'),
    path('technical/', views.technical_list, name='technical_list'),
    path('live/', views.live_control, name='live_control'),
    path('reports/', views.reports, name='reports'),
    path('analytics/', views.analytics, name='analytics'),

    path('stories/', views.story_list, name='story_list'),
    path('stories/create/', views.story_create, name='story_create'),
    path('stories/<slug:slug>/', views.story_detail, name='story_detail'),
    path('stories/<slug:slug>/edit/', views.story_edit, name='story_edit'),
    path('stories/<slug:slug>/ai/', views.story_generate_ai, name='story_generate_ai'),
    path('stories/<slug:slug>/images/upload/', views.image_upload, name='image_upload'),
    path('stories/<slug:slug>/videos/upload/', views.video_upload, name='video_upload'),

    path('programs/', views.program_list, name='program_list'),
    path('programs/create/', views.program_create, name='program_create'),
    path('programs/<int:pk>/edit/', views.program_edit, name='program_edit'),

    path('slots/', views.slot_list, name='slot_list'),
    path('slots/create/', views.slot_create, name='slot_create'),
    path('slots/<int:pk>/edit/', views.slot_edit, name='slot_edit'),

    path('incidents/', views.incident_list, name='incident_list'),
    path('incidents/create/', views.incident_create, name='incident_create'),
    path('incidents/<int:pk>/edit/', views.incident_edit, name='incident_edit'),

    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/create/', views.notification_create, name='notification_create'),
    path('audio/', views.audio_list, name='audio_list'),
    path('audio/create/', views.audio_create, name='audio_create'),
    path('assistant/', views.ai_assistant, name='ai_assistant'),
]

