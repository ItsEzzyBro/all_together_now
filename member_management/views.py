from django.shortcuts import render
from .models import Members

def display_members(request):
    churchmembers = Members.objects.all()
    return render(request, "display_members.html", {"churchmembers": churchmembers})
