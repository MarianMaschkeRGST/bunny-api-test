from django import forms
from .models import Video, Course

class VideoUploadForm(forms.ModelForm):
    """Form for adding and editing videos to course."""
    video_file = forms.FileField()

    def __init__(self, *args, course_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course_id:
            course = Course.objects.get(pk=course_id)
            self.initial['course'] = course



    class Meta:
        model = Video
        fields = ['title', 'course', 'duration', 'description']