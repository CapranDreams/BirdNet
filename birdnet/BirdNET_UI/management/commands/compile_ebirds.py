from django.core.management.base import BaseCommand
from ...eBirdStats import eBirdStats
from ... import settings

class Command(BaseCommand):
    help = 'This command compiles the eBirds database and updates rarity for each species. Recommended: Update rarity every 30 days.'

    def handle(self, *args, **kwargs):
        ebird = eBirdStats(latitude=settings.LATITUDE, longitude=settings.LONGITUDE)

        ebird.build_birds_in_region_db()

        ebird.set_config_compiled(True)

        print("eBirds database compiled and rarity updated")
