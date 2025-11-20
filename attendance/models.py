from django.db import models
from member_management.models import Member

# Create your models here.
class Event(models.Model):
    event_type = models.CharField(max_length = 100)
    event_name = models.CharField(max_length = 100)

    def __str__(self):
        return f"{self.event_name}"

class Attendance(models.Model):
    date = models.DateField()

    attendee = models.ForeignKey(Member, on_delete = models.CASCADE, related_name = 'attendance_records')
    event = models.ForeignKey(Event, on_delete = models.CASCADE, related_name = "attendance_records")

    status_choices = [
        ("P", "Present"),
        ("A", "Absent")
    ]

    status = models.CharField(max_length = 1, choices = status_choices, default = 'P')

    class Meta:
        unique_together = ("attendee", "event")
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        return f"{self.attendee.first_name} {self.attendee.last_name} - {self.event.event_name} ({self.status})"