from django.contrib import admin
from .models import Ministry, MembersAndMinistries

# Register your models here.
@admin.register(Ministry)
class MinistryAdmin(admin.ModelAdmin):
    list_display = ('ministry_name', 'is_active')
    search_fields = ('ministry_name')
    prepopulated_fields = {'slug': ('ministry_name',)}

@admin.register(MembersAndMinistries)
class MembersAndMinistriesAdmin(admin.ModelAdmin):
    list_display = ('member_full_name', 'ministry', 'role')
    list_filter = ('role', 'ministry_name')
    search_fields = ('member__first_name', 'member__last_name', 'ministry_name')
    raw_id_fields = ('member', 'ministry')