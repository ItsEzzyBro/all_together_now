from django.apps import AppConfig

class MemberManagementConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'member_management'

	def ready(self):
		# Ensure Church Administrator role exists at startup
		try:
			from .models import Role
			Role.objects.get_or_create(role_name="Church Administrator")
		except Exception:
			# Silently ignore startup errors (e.g., migrations not yet run)
			pass
