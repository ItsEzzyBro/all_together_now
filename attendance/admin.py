from django.contrib import admin
from .models import Event, EventSchedule, Attendance

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	list_display = ("event_name", "is_active")
	search_fields = ("event_name", "event_description")
	list_filter = ("is_active",)

@admin.register(EventSchedule)
class EventScheduleAdmin(admin.ModelAdmin):
	list_display = ("event", "date", "weekday", "open_time", "close_time")
	list_filter = ("weekday", "date")
	search_fields = ("event__event_name",)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
	list_display = ("attendee", "event", "date", "status")
	list_filter = ("status", "date")
	search_fields = ("attendee__first_name", "attendee__last_name", "event__event_name")