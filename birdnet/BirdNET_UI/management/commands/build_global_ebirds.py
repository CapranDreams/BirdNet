from django.core.management.base import BaseCommand
from BirdNET_UI.eBirdStats import eBirdStats
from django.conf import settings

class Command(BaseCommand):
    help = 'Builds the global eBirds database'

    def handle(self, *args, **kwargs):
        # Initialize eBirdStats with appropriate latitude and longitude
        latitude = settings.LATITUDE
        longitude = settings.LONGITUDE
        ebird_stats = eBirdStats(latitude, longitude)

        # Call the method to build the global eBirds database
        ebird_stats.build_global_ebirds_db()

        self.stdout.write(self.style.SUCCESS('Successfully built the global eBirds database.')) 