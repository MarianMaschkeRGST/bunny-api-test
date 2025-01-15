import sys
import os

from dotenv import load_dotenv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, Sum
from django_filters.views import FilterView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DetailView, DeleteView, View
from django.views.generic.edit import UpdateView
from django.views.decorators.http import require_http_methods

from .forms import CourseForm, VideoUploadForm, VideoUpdateForm
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

class CourseUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "elearning/courses/update.html"
    model = Course
    form_class = CourseForm

    def get_success_url(self):
        return reverse('course_detail', kwargs={
            'pk': self.object.pk,
        })
    
    def form_valid(self, form):
        try:
            if form.cleaned_data['name'] != self.get_object().name:
                stream_library_id = os.getenv('BUNNYCDN_LIBRARY_ID', '')
                api_key = os.getenv('BUNNYCDN_API_KEY', '')
                client = BunnyCDNStream(stream_library_id, api_key)
                
                course = self.get_object()
                
                client.update_collection(
                    collection_id=course.bunny_collection_id,
                    title=form.cleaned_data['name']
                )
            
            messages.success(self.request, 'コース情報を更新しました。')
            return super().form_valid(form)
                
        except Exception as e:
            messages.error(self.request, f'BunnyCDN更新エラー: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '入力内容に誤りがあります。')
        return super().form_invalid(form)
    

class CourseDeleteView(LoginRequiredMixin, DeleteView):
    model = Course
    template_name = 'elearning/courses/delete.html'
    
    def get_success_url(self):
        return reverse('course_index')
    
    def post(self, request, *args, **kwargs):
        course = self.get_object()
        try:
            # Initialize BunnyCDN client
            stream_library_id = os.getenv('BUNNYCDN_LIBRARY_ID', '')
            api_key = os.getenv('BUNNYCDN_API_KEY', '')
            client = BunnyCDNStream(stream_library_id, api_key)
            
            # Delete bunny collection before model
            client.delete_collection(course.bunny_collection_id)
            
            # Delete model
            messages.success(request, f'コース "{course.name}" を削除しました。')
            return super().post(request, *args, **kwargs)
            
        except Exception as e:
            messages.error(request, f'コースの削除に失敗しました: {str(e)}')
            return redirect('course_detail', pk=course.id)


class VideoAddView(LoginRequiredMixin, CreateView):
    template_name = "elearning/videos/add.html"
    form_class = VideoUploadForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['course_id'] = self.kwargs['pk']
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('course_detail', kwargs={'pk': self.object.course.id})

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


class VideoUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "elearning/videos/update.html"
    model = Video
    form_class = VideoUpdateForm
    pk_url_kwarg = 'video_pk'

    def get_success_url(self):
        return reverse('video_detail', kwargs={
            'pk': self.object.course.pk,
            'video_pk': self.object.pk
        })
    
    def get_object(self, queryset=None):
        # Get both course_id and video_id from the URL
        course_id = self.kwargs.get('pk')
        video_id = self.kwargs.get('video_pk')

        return get_object_or_404(Video, course_id=course_id, id=video_id)
    
    def post(self, request, *args, **kwargs):
        if 'sync_duration' in request.POST:
            # Handle duration sync
            video = self.get_object()
            try:
                # Initialize BunnyCDN client
                stream_library_id = os.getenv('BUNNYCDN_LIBRARY_ID', '')
                api_key = os.getenv('BUNNYCDN_API_KEY', '')
                client = BunnyCDNStream(stream_library_id, api_key)
                
                # Get video details from BunnyCDN
                video_details = client.get_video(video.bunny_video_id)
                print(video_details)
                
                duration_seconds = video_details.get('length', 0)
                if duration_seconds > 0:
                    video.duration = duration_seconds
                    video.save(update_fields=['duration'])
                    messages.success(request, f'Duration updated to {video.duration} ')
                else:
                    messages.warning(request, 'Video is still processing, please try again later')
                
            except Exception as e:
                messages.error(request, f'Failed to sync duration: {str(e)}')
            
            return redirect(request.path)
        
        # Handle regular form submission
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        # messages.success(self.request, '動画情報を更新しました。')
        # return super().form_valid(form)
        try:
            if form.cleaned_data['title'] != self.get_object().title:
                stream_library_id = os.getenv('BUNNYCDN_LIBRARY_ID', '')
                api_key = os.getenv('BUNNYCDN_API_KEY', '')
                client = BunnyCDNStream(stream_library_id, api_key)
                
                video = self.get_object()
                
                client.update_video(video_id=video.bunny_video_id ,title=form.cleaned_data['title'],collection_id=video.course.bunny_collection_id)
            
            messages.success(self.request, '動画情報を更新しました。')
            return super().form_valid(form)
                
        except Exception as e:
            messages.error(self.request, f'BunnyCDN更新エラー: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '入力内容に誤りがあります。')
        return super().form_invalid(form)

class VideoDetailView(LoginRequiredMixin, DetailView):
    template_name = "elearning/videos/single.html"
    model = Video
    pk_url_kwarg = 'video_pk' 

    def get_queryset(self):
        return Video.objects.filter(
            course_id=self.kwargs['pk']
        ).select_related('course')
    
class VideoDeleteView(LoginRequiredMixin, DeleteView):
    model = Video
    template_name = 'elearning/videos/delete.html'
    pk_url_kwarg = 'video_pk'
    
    def get_object(self, queryset=None):
        course_id = self.kwargs.get('pk')
        video_id = self.kwargs.get('video_pk')
        return get_object_or_404(Video, course_id=course_id, id=video_id)
    
    def get_success_url(self):
        return reverse('course_detail', kwargs={'pk': self.kwargs.get('pk')})
    
    def post(self, request, *args, **kwargs):
        video = self.get_object()
        try:
            stream_library_id = os.getenv('BUNNYCDN_LIBRARY_ID', '')
            api_key = os.getenv('BUNNYCDN_API_KEY', '')
            client = BunnyCDNStream(stream_library_id, api_key)
            
            # Delete bunny video before model
            client.delete_video(video.bunny_video_id)
            
            # Delete model
            messages.success(request, f'Video "{video.title}" was successfully deleted.')
            return super().post(request, *args, **kwargs)
            
        except Exception as e:
            messages.error(request, f'Failed to delete video: {str(e)}')
            return redirect('video_detail', pk=video.course.id, video_pk=video.id)

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