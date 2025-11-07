from django.urls import path
from . import views

urlpatterns = [
    path('members/', views.display_members, name = 'display_members'),
]