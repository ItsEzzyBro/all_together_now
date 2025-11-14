from django.db import models

# Create your models here.
class Ministry(models.Model):
    ministry_name = models.CharField(max_length = 100, blank = False, null = False)
    slug = models.SlugField(unique = True)
    leader = models.ForeignKey('Member', on_delete=models.SET_NULL, null=True, related_name='ministry_leader')
    is_active = models.BooleanField(default = True)
    members = models.ManyToManyField('Member', through='MembersAndMinistries', related_name='ministry_groups')

    class Meta:
        verbose_name_plural = "Ministries"

    def __str__(self):
        return self.ministry_name

class MembersAndMinistries(models.Model):
    member = models.ForeignKey('Member', on_delete = models.CASCADE, related_name = 'memberships')
    ministry = models.ForeignKey(Ministry, on_delete = models.CASCADE)
    ROLES = [
        ('M', 'Member'),
        ('L', 'Leader'),
    ]
    role = models.CharField(max_length = 1, choices = ROLES, default = 'M')

    class Meta:
        unique_together = ('member', 'ministry')

    def __str__(self):
        return f"{self.member.first_name, self.member.last_name}  - {self.ministry.ministry_name} ({self.role})"

