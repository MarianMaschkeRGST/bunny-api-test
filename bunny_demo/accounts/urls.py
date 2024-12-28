from django.urls import path
 
from . import views
 
# set the application namespace
app_name = 'accounts'
 
urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change/done/', views.PasswordChangeDone.as_view(), name='password_change_done'),
]
