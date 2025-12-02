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
    path("members/", views.members_list, name="members_view"),
    path("visitors/", views.visitors_view, name="visitors"),
    path("ministries/", views.ministries_list, name="ministries"),
    path("attendance/", views.attendance_view, name="attendance"),
    path("analytics/", views.analytics_view, name="analytics"),
    path("system/", views.system_view, name="system"),

    # Account helpers (placeholders)
    path("profile/", views.profile, name="profile"),
    path("change_password/", views.change_password, name="change_password"),

    # Member CRUD
    path("members/new/", views.member_create, name="member_create"),
    path("members/<int:pk>/edit/", views.member_edit, name="member_edit"),
    path("members/<int:pk>/delete/", views.member_delete, name="member_delete"),

    # Ministry CRUD
    path("ministries/new/", views.ministry_create, name="ministry_create"),
    path("ministries/<int:pk>/edit/", views.ministry_edit, name="ministry_edit"),
    path("ministries/<int:pk>/delete/", views.ministry_delete, name="ministry_delete"),
    path("ministries/<int:pk>/create_event/", views.create_event, name="ministry_create_event"),
]
