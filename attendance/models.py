from django.db import models
from member_management.models import Member
from ministry.models import Ministry

# Create your models here.
class Event(models.Model):
    event_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    event_description = models.TextField(blank=True, null=True)
    ministry = models.ForeignKey(Ministry, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')

    def __str__(self):
        return f"{self.event_name}"


class EventSchedule(models.Model):
    WEEKDAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="schedules")

    # One-time occurrence (specific calendar date)
    date = models.DateField(null=True, blank=True)

    # Recurrence by weekday (0-6)
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, null=True, blank=True)

    # Attendance window for this schedule occurrence/pattern
    open_time = models.TimeField()
    close_time = models.TimeField()
    
    @property
    def duration_minutes(self):
        """Calculate duration in minutes between open_time and close_time"""
        from datetime import datetime, timedelta
        open_dt = datetime.combine(datetime.today(), self.open_time)
        close_dt = datetime.combine(datetime.today(), self.close_time)
        if close_dt < open_dt:
            close_dt += timedelta(days=1)
        return int((close_dt - open_dt).total_seconds() / 60)

    class Meta:
        verbose_name = "Event Schedule"
        verbose_name_plural = "Event Schedules"

    def clean(self):
        # Enforce: either date OR weekday must be set (not both null)
        if self.date is None and self.weekday is None:
            raise models.ValidationError("EventSchedule requires either 'date' for one-time events or 'weekday' for recurring events.")
        # If both set, that's ambiguous – restrict to one mode at a time
        if self.date is not None and self.weekday is not None:
            raise models.ValidationError("Provide either 'date' (one-time) or 'weekday' (recurring), not both.")

    def __str__(self):
        if self.date:
            return f"{self.event.event_name} on {self.date} ({self.open_time}-{self.close_time})"
        weekday_label = dict(self.WEEKDAY_CHOICES).get(self.weekday, "?")
        return f"{self.event.event_name} every {weekday_label} ({self.open_time}-{self.close_time})"

    def is_open_now(self, current_dt=None):
        """
        Returns True if attendance is currently open for this schedule.
        - For one-time (date): current date must match `date`, and time within [open_time, close_time].
        - For recurring (weekday): current weekday must match, and time within window.
        """
        from datetime import datetime

        # Use naive datetime in server time or provide current_dt
        if current_dt is None:
            current_dt = datetime.now()

        current_date = current_dt.date()
        current_time = current_dt.time()

        # Check time window
        if not (self.open_time <= current_time <= self.close_time):
            return False

        # One-time date schedule
        if self.date is not None:
            return current_date == self.date

        # Recurring weekday schedule
        if self.weekday is not None:
            if current_dt.weekday() != self.weekday:
                return False
            return True

        # Neither mode set (should be prevented by clean), but be safe
        return False

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