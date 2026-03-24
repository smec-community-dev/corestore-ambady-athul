from django.urls import path
from .import views

urlpatterns = [
     path("login/",views.adminlogin),
    path("adminhome/",views.adminhome),
]