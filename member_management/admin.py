from django.contrib import admin
from .models import Member, Family, Vistor

# Register your models here.
class MemberAdmin(admin.ModelAdmin):
    list_display = ()
    list_filter = ('last_name', 'gender')
    search_fields = ('last_name', 'gender')
    ordering = ['last_name']
    list_display_links = ()
    list_editable = ()
    readonly_fields = []

    def display_age(self, obj):
        return obj.age
    display_age.short_description = "Age"

admin.site.register(Member, MemberAdmin)
admin.site.register(Family)
admin.site.register(Vistor)