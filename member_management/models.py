from django.db import models
from datetime import date
from dateutil.relativedelta import relativedelta

# Create your models here.
class Member(models.Model):
    first_name = models.CharField(max_length = 100, blank = False, null = False)
    last_name = models.CharField(max_length = 100, blank = False, null = False)
    date_of_birth = models.DateField(blank = False, null = True, verbose_name = "Date of Birth", help_text="Provide the member's date of birth (MM/DD/YYYY).")
    GENDER = [
        ("M", "Male"),
        ("F", "Female")
    ]
    gender = models.CharField(max_length = 1, choices = GENDER, blank = True, null = True)

    MARITAL_STATUS = [
        ("S", "Single"),
        ("M", "Married"),
        ("D", "Divorced"),
        ("W", "Widowed")
    ]
    marital_status = models.CharField(max_length = 1, choices = MARITAL_STATUS, blank = True, null = True, default = 'S')
    address = models.TextField(blank = True, null = True)
    phone_number = models.CharField(max_length = 25, blank = True, null = True)
    email = models.EmailField(unique = True, blank = True, null = True)

    family = models.ForeignKey('Family', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')

    def calculate_age(self):
        today = date.today()
        age_calculated = relativedelta(today, self.date_of_birth)

        return age_calculated.years
    
    @property
    def age(self):
        return self.calculate_age()


    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        verbose_name = "Member"
        verbose_name_plural = "Members"


class Family(models.Model):
    family_name = models.CharField(max_length=100)

    def __str__(self):
        return f"The {self.family_name} Family"
    
    class Meta:
        verbose_name = "Family"
        verbose_name_plural = "Families"
    

class Vistor(models.Model):
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length = 100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        verbose_name = "Vistor"
        verbose_name_plural = "Vistors"