from django.urls import path

from . import views

urlpatterns = [
    path("courses/", views.CourseIndexView.as_view(), name="course_index"),
    path("create/", views.create, name="videos_create"),
]