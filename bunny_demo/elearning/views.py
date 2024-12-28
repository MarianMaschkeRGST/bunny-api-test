import sys
import ffmpeg
import os
from dotenv import load_dotenv
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import FileSystemStorage
from django_filters.views import FilterView
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import DetailView, TemplateView, DeleteView
from django.views.generic.edit import FormView, UpdateView
from django.views.decorators.http import require_http_methods

from .forms import VideoUploadForm
from .models import Course, Video
from libs.utils import BunnyCDNStream


# Load environment variables from .env file
load_dotenv()

# Check for required environment variables
required_env_vars = [
'BUNNYCDN_LIBRARY_ID',
'BUNNYCDN_API_KEY',
]

for var in required_env_vars:
    if not os.getenv(var):
        raise Exception(f'{var} environment variable is not set.')

# Views
# def index(request):
#     return render(request, 'videos/index.html')


# class VideoListview(LoginRequiredMixin, TemplateView):
#     template_name = "videos/index"

#     def get_context_data(self, **kwargs) -> dict[str, Any]:
#         context = super().get_context_data(**kwargs)

#         try:
#             # Get Video collection from bunny
#             # Initialize BunnyCDN client
#             stream_library_id = os.getenv('BUNNYCDN_LIBRARY_ID', '')
#             api_key = os.getenv('BUNNYCDN_API_KEY', '')
            
#             client = BunnyCDNStream(stream_library_id, api_key)

#             # Create video entry
#             response = client.list_videos(collection_id="bda9f79b-419d-46ff-b19b-c3808870befc")

#             videos = []

#             context.update(response)
                            
#         except Exception as e:
#             print(f"Error fetching PayPal invoices: {str(e)}")
#             if hasattr(e, 'response'):
#                 print(f"Response Status: {e.response.status_code}")
#                 print(f"Response Body: {e.response.text}")
                
#             return context

class CourseIndexView(LoginRequiredMixin, FilterView):
    
    paginate_by = None
    template_name = "elearning/courses/index.html"
    model = Course
    queryset = Course.objects.all().order_by('-created_at')

        
def create_and_upload_video(title, collection_id, file_path=None):
    """
    Creates and optionally uploads a video to BunnyCDN.
    """
    try:
        # Initialize BunnyCDN client
        stream_library_id = os.getenv('BUNNYCDN_LIBRARY_ID', '')
        api_key = os.getenv('BUNNYCDN_API_KEY', '')
        
        client = BunnyCDNStream(stream_library_id, api_key)
        
        # Create video entry
        response = client.create_video(title, collection_id)
        
        # If a file path is provided, upload the video
        if file_path and response.get('guid'):
            upload_response = client.upload_video_with_id(response['guid'], file_path)
            return upload_response
            
        return response
        
    except Exception as e:
        raise Exception(f"Failed to create/upload video: {str(e)}")


@require_http_methods(["GET", "POST"])
def create(request):
    if request.method == "GET":
        form = VideoUploadForm()
        return render(request, "videos/create.html", {"form": form})
    elif request.method == "POST":
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video_file = form.cleaned_data["video_file"]
            video_title = form.cleaned_data["title"]

            fs = FileSystemStorage()
            filename = fs.save(video_file.name, video_file)
            file_path = fs.path(filename)

            try:
                response = create_and_upload_video(video_title,"bda9f79b-419d-46ff-b19b-c3808870befc", file_path)
                return redirect('videos_index')
            except Exception as e:
                print(e, file=sys.stderr)
                fs.delete(filename)
                return HttpResponse("Something went wrong", status=500)
            finally:
                cleanup_files(fs, filename)

def print_debug_info(url):
    print("*" * 20)
    print(url)
    print("*" * 20)

def cleanup_files(fs, *file_paths):
    for path in file_paths:
        fs.delete(path)