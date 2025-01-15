from django.urls import path

from . import views

urlpatterns = [
    path("courses/", views.CourseIndexView.as_view(), name="course_index"),
    path("courses/add", views.CourseAddView.as_view(), name="course_add"),
    path("courses/<int:pk>/", views.CourseDetailView.as_view(), name="course_detail"),
    path("courses/<int:pk>/videos/add/", views.VideoAddView.as_view(), name="video_add"),
    path("courses/<int:pk>/videos/<int:video_pk>/", views.VideoDetailView.as_view(), name="video_detail"),
    path("courses/<int:pk>/videos/<int:video_pk>/update/", views.VideoUpdateView.as_view(), name="video_update"),
    path("courses/<int:pk>/videos/<int:video_pk>/delete/", views.VideoDeleteView.as_view(), name="video_delete"),
    path('courses/<int:pk>/videos/<int:video_pk>/progress/', views.VideoProgressUpdateView.as_view(), name='video_progress_update'),
    path("create/", views.create, name="videos_create"),
]