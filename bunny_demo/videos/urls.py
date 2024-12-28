from django.urls import path

from .views import index, create

urlpatterns = [
    path("", index, name="videos_index"),
    path("create/", create, name="videos_create"),
]