from django.db import models

# Create your models here.
class Members(models.Model):
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length = 100)
    date_of_birth = models.DateField()
    marital_status = models.CharField(max_length = 50)
    address = models.CharField(max_length = 100)
    phone_number = models.CharField(max_length = 50)
    gender = models.CharField(max_length = 50)

    def __str__(self):
        return "f{self.first_name} {self.last_name}"