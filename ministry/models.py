from django.db import models
from member_management.models import Member

# Create your models here.
class Ministry(models.Model):
    ministry_name = models.CharField(max_length = 100, unique = True)
    is_active = models.BooleanField(default = True)
    
    leader = models.ForeignKey(Member, on_delete = models.SET_NULL, null = True, blank = True)

    members = models.ManyToManyField(Member, through = "MembersAndMinistries", related_name = "church_groups")

    class Meta:
        verbose_name_plural = "Ministries"

    def __str__(self):
        return self.ministry_name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure Church Administrator role has access to this ministry
        try:
            from member_management.models import Role, RolesAndMinistries
            admin_role, _ = Role.objects.get_or_create(role_name="Church Administrator")
            RolesAndMinistries.objects.get_or_create(role=admin_role, ministry=self)
        except Exception:
            # Silently pass if models aren't ready yet (e.g., during migrations)
            pass
    
class MembersAndMinistries(models.Model):
    member = models.ForeignKey(Member, on_delete = models.CASCADE)
    ministry = models.ForeignKey(Ministry, on_delete = models.CASCADE)
    role = models.CharField(max_length = 50, choices = [("Member", "Member"), ("Leader", "Leader")], default = "Member")

    class Meta:
        unique_together = ("member", "ministry")
        verbose_name = "Ministry Membership"
        verbose_name_plural = "Ministry Memberships"

