# members/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("connection_card/", views.connection_card, name="connection_card"),

    # Auth-required
    path("dashboard/", views.dashboard, name="dashboard"),
    path("members/", views.members_view, name="members"),
    path("visitors/", views.visitors_view, name="visitors"),
    path("ministries/", views.ministries_view, name="ministries"),
    path("attendance/", views.attendance_view, name="attendance"),
    path("analytics/", views.analytics_view, name="analytics"),
    path("system/", views.system_view, name="system"),

    # Account helpers (placeholders)
    path("profile/", views.profile, name="profile"),
    path("change_password/", views.change_password, name="change_password"),
]
