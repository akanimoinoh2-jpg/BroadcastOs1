from django.contrib import admin

from .models import BroadcastSlot, Program, UserProfile, Story


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    search_fields = ('user__username', 'user__email', 'role')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'producer', 'start_time', 'end_time', 'status')
    list_filter = ('status',)
    search_fields = ('title', 'description', 'producer__username')


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'assigned_to', 'created_at', 'published_at')
    list_filter = ('status',)
    search_fields = ('title', 'slug', 'body')
    readonly_fields = ('headline_suggestions', 'suggested_tags', 'ai_notes')


@admin.register(BroadcastSlot)
class BroadcastSlotAdmin(admin.ModelAdmin):
    list_display = ('program', 'story', 'scheduled_time', 'duration_minutes')
    list_filter = ('scheduled_time',)
    search_fields = ('program__title', 'story__title', 'studio')
