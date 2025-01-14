from django.contrib import admin

# Register your models here.
from .models import Course, Video, VideoProgress

admin.site.register(Course)
admin.site.register(Video)

@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'watch_progress', 'updated_at')
    list_filter = ('user', 'video', 'watch_progress')
    search_fields = ('user__username', 'video__title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user', 'video')
        return self.readonly_fields