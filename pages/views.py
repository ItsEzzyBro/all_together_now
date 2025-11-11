from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
def main_page(request):
    return render(request, "main.html")

@login_required
def home_page(request):
    return render(request, "home.html")