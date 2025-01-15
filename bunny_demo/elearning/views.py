import json
import sys
import ffmpeg
import os
from dotenv import load_dotenv
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, Sum
from django_filters.views import FilterView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import CreateView, DetailView, TemplateView, DeleteView, View
from django.views.generic.edit import FormView, UpdateView
from django.views.decorators.http import require_http_methods

from .forms import CourseForm, VideoUploadForm
from .filters import CourseFilter
from .models import Course, Video, VideoProgress
from libs.utils import BunnyCDNStream

from django.contrib import messages
from django.urls import reverse_lazy, reverse

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
    
    # For django-filter
    filterset_class = CourseFilter
    strict = False

    def get_queryset(self):
        return Course.objects.annotate(
            video_count=Count('video'),
            total_duration=Sum('video__duration')
        ).order_by('-created_at')


class CourseAddView(LoginRequiredMixin, CreateView):
    template_name = "elearning/courses/add.html"
    form_class = CourseForm
    
    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        
        try:
            bunny_response = create_collection(title=form.cleaned_data['name'])
            
            print("Full BunnyCDN response:", bunny_response) 
            
            if 'guid' not in bunny_response:
                raise Exception(f"Missing video ID in BunnyCDN response: {bunny_response}")

            # Save course with bunny_course_id
            course = form.save(commit=False)
            course.bunny_collection_id = bunny_response['guid']
            course.save()

            messages.success(self.request, "Collection created successfully")
            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, f"Collection creation failed: {str(e)}")
            return self.form_invalid(form)
    

class CourseDetailView(LoginRequiredMixin, DetailView):

    template_name = "elearning/courses/single.html"
    model = Course

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get facilities
        context['videos'] = Video.objects.filter(course=context['course']).order_by('-created_at')
        return context


class VideoAddView(LoginRequiredMixin, CreateView):
    template_name = "elearning/videos/add.html"
    form_class = VideoUploadForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course_id'] = self.kwargs['pk']
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'pk': self.object.course.id})
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # Add course selection to the template context
    #     context['courses'] = Course.objects.all().order_by('-created_at')
    #     return context

    def form_valid(self, form):
        video_file = self.request.FILES['video_file']
        
        # Save file temporarily
        fs = FileSystemStorage()
        filename = fs.save(video_file.name, video_file)
        file_path = fs.path(filename)

        try:
            # Upload to BunnyCDN
            bunny_response = create_and_upload_video(
                title=form.cleaned_data['title'],
                collection_id=form.cleaned_data['course'].bunny_collection_id,
                file_path=file_path
            )
            
            print("Full BunnyCDN response:", bunny_response)  # Debug print
            
            if 'guid' not in bunny_response:
                raise Exception(f"Missing video ID in BunnyCDN response: {bunny_response}")

            # Save video with bunny_video_id
            video = form.save(commit=False)
            video.bunny_video_id = bunny_response['guid']
            video.save()

            messages.success(self.request, "Video uploaded successfully")
            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, f"Upload failed: {str(e)}")
            return self.form_invalid(form)

        finally:
            # Clean up temporary file
            cleanup_files(fs, filename)



class VideoDetailView(LoginRequiredMixin, DetailView):

    template_name = "elearning/videos/single.html"
    model = Video
    pk_url_kwarg = 'video_pk' 

    def get_queryset(self):
        return Video.objects.filter(
            course_id=self.kwargs['pk']
        ).select_related('course')


class VideoProgressUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, video_pk):
        try:
            video = Video.objects.get(course_id=pk, pk=video_pk)
            watch_progress = int(request.POST.get('watch_progress', 0))

            print(f"Received progress update: {watch_progress}%")  # Debug print
            
            # Validate progress is between 0 and 100
            watch_progress = max(0, min(100, watch_progress))
            
            # Get or create progress record for this user and video
            video_progress, created = VideoProgress.objects.get_or_create(
                user=request.user,
                video=video,
                defaults={'watch_progress': watch_progress}
            )
            
            # Update progress if higher than existing 
            if not created and watch_progress > video_progress.watch_progress:
                video_progress.watch_progress = watch_progress
                video_progress.save(update_fields=['watch_progress', 'updated_at'])
            
            print(f"Saved progress: {video_progress.watch_progress}%")  # Debug print
            
            # Include redirect URL in JSON response
            success_url = reverse('course_detail', kwargs={'pk': video.course_id})
                
                
            response = JsonResponse({
                'success': True,
                'progress': watch_progress,
                'message': f'Progress updated to {watch_progress}%',
                'redirect_url': success_url
            })

            # Redirect on success - weird UX
            # response['HX-Redirect'] = reverse('course_detail', kwargs={'pk': pk})
            return response
            
        except Exception as e:
            print(f"Error saving progress: {str(e)}") 
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# https://docs.bunny.net/reference/collection_createcollection
def create_collection(title):
    """
    Creates a Collection in Bunny.
    """
    try:
        # Initialize BunnyCDN client
        stream_library_id = os.getenv('BUNNYCDN_LIBRARY_ID', '')
        api_key = os.getenv('BUNNYCDN_API_KEY', '')

        client = BunnyCDNStream(stream_library_id, api_key)

        response = client.create_collection(title)
        print("BunnyCDN create_collection response:", response)

        return response
        
    except Exception as e:
        print(f"BunnyCDN Error: {str(e)}")  # Debug print
        if hasattr(e, 'response'):
            print(f"Response Status: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        raise Exception(f"Failed to create collection: {str(e)}")

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
        print("BunnyCDN create_video response:", response)  # Debug print
        
        # If a file path is provided, upload the video
        if file_path and response.get('guid'):
            upload_response = client.upload_video_with_id(response['guid'], file_path)
            print("BunnyCDN upload_response:", upload_response)  # Debug print
            return response  # Return original response with guid
            
        return response
        
    except Exception as e:
        print(f"BunnyCDN Error: {str(e)}")  # Debug print
        if hasattr(e, 'response'):
            print(f"Response Status: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        raise Exception(f"Failed to create/upload video: {str(e)}")


@require_http_methods(["GET", "POST"])
def create(request):
    if request.method == "GET":
        form = VideoUploadForm()
        return render(request, "videos/add.html", {"form": form})
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