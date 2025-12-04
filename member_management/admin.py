from django.contrib import admin
from .models import Member, Family, Vistor, Role, UsersAndRoles, RolesAndMinistries

# Register your models here.
class MemberAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "display_age")
    list_filter = ('last_name', 'gender')
    search_fields = ('last_name', 'gender')
    list_display_links = ()
    list_editable = ()
    readonly_fields = []

    def display_age(self, obj):
        return obj.age
    display_age.short_description = "Age"

class VistorAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "display_age")
    list_filter = ('last_name', 'gender')
    search_fields = ('last_name', 'gender')
    list_display_links = ()
    list_editable = ()
    readonly_fields = []

    
    def display_age(self, obj):
        return obj.age
    display_age.short_description = "Age"

admin.site.register(Member, MemberAdmin)
admin.site.register(Family)
admin.site.register(Vistor, VistorAdmin)
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("role_name",)
    search_fields = ("role_name",)

@admin.register(RolesAndMinistries)
class RolesAndMinistriesAdmin(admin.ModelAdmin):
    list_display = ("role", "ministry")
    list_filter = ("ministry", "role")
    search_fields = ("role__role_name", "ministry__ministry_name")

@admin.register(UsersAndRoles)
class UsersAndRolesAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "role__role_name")