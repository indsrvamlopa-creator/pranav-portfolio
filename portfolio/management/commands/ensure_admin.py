"""Create (or update) the admin login from environment variables.

Safe to run on every deploy, e.g. in Render's Build Command:
    python manage.py ensure_admin

Reads:
    DJANGO_SUPERUSER_USERNAME   (required)
    DJANGO_SUPERUSER_PASSWORD   (required)
    DJANGO_SUPERUSER_EMAIL      (optional)
If the variables are missing it just skips — it never fails the build.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the admin superuser from DJANGO_SUPERUSER_* environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        if not username or not password:
            self.stdout.write(self.style.WARNING(
                "ensure_admin: DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD not set - skipped."))
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if email:
            user.email = email
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"ensure_admin: superuser '{username}' {'created' if created else 'updated'}."))
