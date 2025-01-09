from django import forms
from .models import Video

class VideoUploadForm(forms.ModelForm):
    video_file = forms.FileField()
    
    class Meta:
        model = Video
        fields = ['title', 'course']