from django.core.management.base import BaseCommand
from ...models import eBirds, Bird, EBirdsExtra
from ...bird_data_scraper import BirdDataScraper
import time

class Command(BaseCommand):
    help = 'Compile additional bird data from All About Birds'

    def add_arguments(self, parser):
        # Add an argument to clear the old ebirds_extra table
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear the old ebirds_extra table before processing new data'
        )

    def handle(self, *args, **kwargs):
        # Check if the clear argument is provided
        if kwargs['clear']:
            print("Clearing the old ebirds_extra table...")
            EBirdsExtra.objects.using('ebirds').all().delete()  # Clear the table
            self.stdout.write(self.style.SUCCESS("Cleared the old ebirds_extra table."))

        self.stdout.write("Starting compilation of ebirds_extra table...")
        self.stdout.write("This may take a while (1hr+)...")
        
        # Get all birds from ebirds and birds tables
        ebirds = list(eBirds.objects.using('ebirds').values('scientific_name', 'common_name').distinct())
        birds = list(Bird.objects.using('birds').values('scientific_name', 'common_name').distinct())
        existing_birds = list(EBirdsExtra.objects.using('ebirds').values('scientific_name', 'common_name').distinct())
        
        print(f"Number of existing birds in ebirds_extra: {len(existing_birds)}")
        print(f"Number of birds in ebirds table: {len(ebirds)}")
        print(f"Number of birds in birds table: {len(birds)}")
        
        # Initialize scraper
        scraper = BirdDataScraper()
        
        # combine the two dictionaries
        all_birds = ebirds + birds

        # remove entries that are already in the ebirds_extra table, leave as dictionary
        new_birds = [bird for bird in all_birds if bird not in existing_birds]
                
        # Process new birds
        self.stdout.write(self.style.SQL_KEYWORD(f"Processing {len(new_birds)} new birds..."))
        for i, bird in enumerate(new_birds):
            print(f"Processing {i+1}/{len(new_birds)}: {bird['scientific_name']} ({bird['common_name']})")
            self._process_bird(
                bird['scientific_name'], 
                bird['common_name'], 
                existing_birds, 
                scraper,
                i + 1,
                len(new_birds)
            )
            # Be nice to the server
            time.sleep(1)
            
        self.stdout.write(self.style.SUCCESS("Compilation complete!"))
    
    def _process_bird(self, scientific_name, common_name, existing_birds, scraper, current, total):
        """Process a single bird entry"""
        self.stdout.write(f"Processing {current}/{total}: {common_name} ({scientific_name})")
        
        # Skip if already exists
        if scientific_name in existing_birds:
            self.stdout.write(f"  Already exists, updating only if needed")
            bird_extra = existing_birds[scientific_name]
            
            # Only update if fields are empty
            needs_update = False
            if not bird_extra.ideal_audio or not bird_extra.range_map:
                needs_update = True
                
            if not needs_update:
                return
        else:
            # Create new entry
            bird_extra = EBirdsExtra(
                scientific_name=scientific_name,
                common_name=common_name,
                best_audio='',
                ideal_audio='',
                range_map='',
                migration_description='',
                description='',
                tips='',
                find_this_bird='',
                habitat_value='',
                food_value='',
                nesting_value='',
                behavior_value='',
                conservation_value=''
            )
        
        try:
            # Get all bird data from the scraper
            bird_data = scraper.get_ebird_extras(common_name)
            
            # Update the bird_extra object with all the data
            if bird_data.get('audio_url'):
                bird_extra.ideal_audio = bird_data['audio_url']
                # self.stdout.write(f"  Found ideal audio: {bird_data['audio_url']}")
                
            if bird_data.get('range_map_url'):
                bird_extra.range_map = bird_data['range_map_url']
                # self.stdout.write(f"  Found range map: {bird_data['range_map_url']}")
                
            # Add all the other fields
            if bird_data.get('migration_description'):
                bird_extra.migration_description = bird_data.get('migration_description', '')
            if bird_data.get('description'):
                bird_extra.description = bird_data.get('description', '')
            if bird_data.get('tips'):
                bird_extra.tips = bird_data.get('tips', '')
            if bird_data.get('find_this_bird'):
                bird_extra.find_this_bird = bird_data.get('find_this_bird', '')
            if bird_data.get('habitat_value'):
                bird_extra.habitat_value = bird_data.get('habitat_value', '')
                bird_extra.food_value = bird_data.get('food_value', '')
                bird_extra.nesting_value = bird_data.get('nesting_value', '')
                bird_extra.behavior_value = bird_data.get('behavior_value', '')
                bird_extra.conservation_value = bird_data.get('conservation_value', '')
            
            # Save the entry
            bird_extra.save(using='ebirds')
            self.stdout.write(self.style.SUCCESS(f"  Successfully saved data for {common_name}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error processing {common_name}: {str(e)}")) 