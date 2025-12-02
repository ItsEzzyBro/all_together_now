# members/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# ---------- Public pages ----------
def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def contact(request):
    return render(request, "contact.html")

def connection_card(request):
    return render(request, "connection_card.html")

# ---------- Auth-required pages ----------
@login_required
def dashboard(request):
    return render(request, "dashboard.html")

@login_required
def members_view(request):
    return render(request, "members.html")

@login_required
def visitors_view(request):
    return render(request, "visitors.html")

@login_required
def ministries_view(request):
    return render(request, "ministries.html")

@login_required
def attendance_view(request):
    return render(request, "attendance.html")

@login_required
def analytics_view(request):
    return render(request, "analytics.html")

@login_required
def system_view(request):
    return render(request, "system.html")

@login_required
def profile(request):
    # You can create a dedicated template later; using dashboard for now
    return render(request, "dashboard.html")

@login_required
def change_password(request):
    # You can wire Django's PasswordChangeView later; placeholder template for now
    return render(request, "dashboard.html")
