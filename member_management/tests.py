from django.test import TestCase
from .models import Members
from django.urls import reverse

class MembersViewTests(TestCase):
    def test_members_page_loads(self):
        Members.objects.create(
            first_name="Matthew",
            last_name="Orellana",
        )
        resp = self.client.get(reverse("display_members"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "John Doe")
