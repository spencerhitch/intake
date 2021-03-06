from django.core.management.base import BaseCommand

from django.conf import settings

from intake import models


class Command(BaseCommand):
    help = 'Sends an email about unopened applications'

    def handle(self, *args, **options):
        models.FormSubmission.refer_unopened_apps()
        self.stdout.write(
            self.style.SUCCESS("Successfully referred any unopened apps")
            )