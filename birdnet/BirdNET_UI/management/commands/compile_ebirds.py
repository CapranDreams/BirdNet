from django.core.management.base import BaseCommand
# import os
# import json
# import time
# import shutil

# from datetime import datetime
# from apscheduler.schedulers.background import BackgroundScheduler
# from ...models import eBirds, eBirdsConfig
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
from ...eBirdStats import eBirdStats


class Command(BaseCommand):
    help = 'This command compiles the eBirds database and updates rarity for each species. Recommended: Update rarity every 30 days.'

    def handle(self, *args, **kwargs):
        ebird = eBirdStats(latitude=45.080681, longitude=-92.898758)

        ebird.build_birds_in_region_db()

        ebird.set_config_compiled(True)

        print("eBirds database compiled and rarity updated")
