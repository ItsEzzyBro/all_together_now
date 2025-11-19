from django.db import models
from member_management.models import Member

# Create your models here.
class Events(models.Model):
    event_type = models.CharField(max_length = 100)
    event_name = models.CharField(max_length = 100)

    def __str__(self):
        return self.event_name

class Attendance(models.Model):
    date = models.DateField()

    def __str__(self):
        return 