"""Seed an admin user + initial agent-health rows so the demo is ready on boot."""
from agents import AGENT_REGISTRY
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import AgentHealth


class Command(BaseCommand):
    help = "Seed demo data (admin user + healthy agent rail)."

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@ecoti.local", "admin")
            self.stdout.write(self.style.SUCCESS("Created superuser admin/admin"))

        for name in AGENT_REGISTRY:
            if not AgentHealth.objects.filter(agent=name).exists():
                AgentHealth.objects.create(agent=name, status="healthy", detail="seeded")
        self.stdout.write(self.style.SUCCESS("Seeded agent health rail."))
        self.stdout.write(
            "Demo identifier: +919812345678 (seeded mule cluster + scam script)."
        )
