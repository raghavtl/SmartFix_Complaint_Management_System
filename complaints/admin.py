from django.contrib import admin, messages
from .models import Complaint, Profile, Comment, Notification


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'dark_mode', 'profile_pic')
    search_fields = ('user__username', 'phone')
    list_select_related = ('user',)

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'priority', 'status', 'user', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'description', 'user__username', 'assigned_to__username')
    readonly_fields = ('created_at', 'updated_at', 'quick_summary')
    ordering = ('-created_at',)
    list_select_related = ('user', 'assigned_to')
    list_per_page = 25
    actions = ('mark_assigned', 'mark_in_progress', 'mark_resolved', 'mark_rejected')
    fieldsets = (
        ('Complaint Details', {
            'fields': (
                'quick_summary',
                'user',
                'is_anonymous',
                'title',
                'category',
                'description',
                'location',
                'image',
            )
        }),
        ('Operations', {
            'fields': ('priority', 'status', 'assigned_to')
        }),
        ('Timeline', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    @admin.display(description='Quick summary')
    def quick_summary(self, obj):
        return (
            f'#{obj.id} | {obj.title} | Priority: {obj.priority} | '
            f'Status: {obj.status} | Reporter: {obj.display_user}'
        )

    @admin.action(description='Set selected complaints to Assigned')
    def mark_assigned(self, request, queryset):
        updated = queryset.update(status='Assigned')
        self.message_user(request, f'{updated} complaint(s) marked as Assigned.', messages.SUCCESS)

    @admin.action(description='Set selected complaints to In Progress')
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status='In Progress')
        self.message_user(request, f'{updated} complaint(s) marked as In Progress.', messages.SUCCESS)

    @admin.action(description='Set selected complaints to Resolved')
    def mark_resolved(self, request, queryset):
        updated = queryset.update(status='Resolved')
        self.message_user(request, f'{updated} complaint(s) marked as Resolved.', messages.SUCCESS)

    @admin.action(description='Set selected complaints to Rejected')
    def mark_rejected(self, request, queryset):
        updated = queryset.update(status='Rejected')
        self.message_user(request, f'{updated} complaint(s) marked as Rejected.', messages.WARNING)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'admin', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('complaint__title', 'admin__username', 'message')
    list_select_related = ('complaint', 'admin')
    list_per_page = 25

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    list_select_related = ('user',)
    list_per_page = 25
