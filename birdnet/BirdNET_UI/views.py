import os
from django.shortcuts import render
from django.conf import settings
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from datetime import datetime, timedelta
from django.http import JsonResponse, FileResponse, Http404, StreamingHttpResponse
from .models import Bird, BirdNow, WavSpectrogram, eBirds, eBirdsConfig, Config
import time
from BirdNET_UI.management.commands.start_file_listener import FileHandler
from django.forms.models import model_to_dict
from BirdNET_UI.eBirdStats import eBirdStats
import json
from django.views.decorators.csrf import csrf_exempt
import subprocess
from django.db.models import Count
from django.db.models.functions import TruncWeek, TruncYear
import traceback

def serve_index(request):
    return render(request, 'BirdNET_UI/index.html')

def get_birds(request):
    try:
        birds = Bird.objects.using('birds').all()  # Use Django ORM to fetch all birds
        birds_data = [
            {
                'scientific_name': bird.scientific_name,
                'common_name': bird.common_name,
                'confidence': bird.confidence,
                'sighting_time': bird.sighting_time,
                'location_name': bird.location_name,
                'latitude': bird.latitude,
                'longitude': bird.longitude,
            }
            for bird in birds
        ]
        return JsonResponse(birds_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_birds_now(request):
    try:
        print("get_birds_now view called")
        birds = BirdNow.objects.using('birds').all()  # Use Django ORM to fetch all birds now
        birds_now_data = [
            {
                'scientific_name': bird.scientific_name,
                'common_name': bird.common_name,
                'confidence': bird.confidence,
                'sighting_time': bird.sighting_time,
            }
            for bird in birds
        ]
        return JsonResponse(birds_now_data, safe=False)
    except Exception as e:
        print(f"Error in get_birds_now view: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

def get_detections_this_week(request):
    try:
        history_days = int(get_history_days())
        print(f"get_detections_this_week view called (check for birds in the last {history_days} days)")
        confidence_threshold = float(get_config_value('confidence_threshold'))
        birds = Bird.objects.using('birds').filter(sighting_time__gte=datetime.now() - timedelta(days=history_days), confidence__gte=confidence_threshold)  # Use Django ORM
        print(f"birds in last {history_days} days: {len(birds)}")
        
        # Check if any birds were found
        if not birds:
            print("No birds detected this week")
            return JsonResponse({'error': "No birds detected this week"}, safe=False)

        # Initialize a dictionary to count detections per hour for each bird type
        detections_count = {}

        for bird in birds:
            common_name = bird.common_name
            hour = bird.sighting_time.hour
            
            if common_name not in detections_count:
                detections_count[common_name] = [0] * 24  # Initialize a list for each hour of the day
            
            detections_count[common_name][hour] += 1  # Increment the count for the specific hour

        # Convert the dictionary to a 2D array
        detections_this_week_data = [
            [common_name] + counts for common_name, counts in detections_count.items()
        ]

        # sort detections_this_week_data based on the detections_this_week_data_sum
        detections_this_week_data.sort(key=lambda x: sum(x[1:]), reverse=True)

        # Return the data as JSON
        # print("detections_this_week_data: ", detections_this_week_data)
        return JsonResponse(detections_this_week_data, safe=False)
    except Exception as e:
        print(f"Error in get_detections_this_week view: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

def get_detections_this_week_genus_only(request):
    detections = json.loads(get_detections_this_week(request).content)
    
    # consolidate bird names into genus while keeping the detections by hour
    detections_genus_only = {}
    for detection in detections:
        # get the eBird of the bird common name
        ebird = find_ebird_by_word(detection[0])
        if ebird:
            genus = get_genus(ebird.scientific_name)
            if genus not in detections_genus_only:
                detections_genus_only[genus] = detection[1:]
            else:
                detections_genus_only[genus] += detection[1:]
        else:
            print(f"No eBird found for {detection[0]}")

    detections_genus_only_json = []
    for genus, detections in detections_genus_only.items():
        detections_genus_only_json.append([genus] + detections)

    # sort detections_genus_only_json by the total detections
    detections_genus_only_json.sort(key=lambda x: sum(x[1:]), reverse=True)

    return JsonResponse(detections_genus_only_json, safe=False)

def get_detections_this_week_second_name_only(request):
    # do the same thing as get_detections_this_week_genus_only but use the common name instead of the scientific name
    detections = json.loads(get_detections_this_week(request).content)
    
    # consolidate bird names into genus while keeping the detections by hour
    detections_genus_only = {}
    for detection in detections:
        genus = get_family(detection[0]) # not really the family, but effectively the genus based on common name
        if genus not in detections_genus_only:
            detections_genus_only[genus] = detection[1:]
        else:
            detections_genus_only[genus] += detection[1:]

    detections_genus_only_json = []
    for genus, detections in detections_genus_only.items():
        detections_genus_only_json.append([genus] + detections)

    # sort detections_genus_only_json by the total detections
    detections_genus_only_json.sort(key=lambda x: sum(x[1:]), reverse=True)

    return JsonResponse(detections_genus_only_json, safe=False)

def get_config_value(key, default=None):
    """
    Get a configuration value from the birds.db config table.
    Falls back to default if the key doesn't exist or there's an error.
    """
    try:
        config = Config.objects.using('birds').filter(key=key).first()
        if config:
            return config.value
        return default
    except Exception as e:
        print(f"Error retrieving config value for {key}: {e}")
        return default

def get_history_days():
    """
    Get the history_days value from the config table.
    """
    try:
        value = get_config_value('history_days')
        if value:
            return int(value)
        return settings.BIRDNET_WEB_HISTORY_DAYS_IN_OBSERVATIONS_TABLE
    except Exception as e:
        print(f"Error retrieving history_days: {e}")
        return settings.BIRDNET_WEB_HISTORY_DAYS_IN_OBSERVATIONS_TABLE

def get_observation_history_days(request):
    history_days = get_history_days()
    print(f"get_observation_history_days: {history_days} days")
    return JsonResponse({'history_days': history_days}, safe=False)

def get_lat_and_long():
    """
    Get the latitude and longitude from the config table.
    """
    try:
        this_latitude = get_config_value('latitude')
        this_longitude = get_config_value('longitude')
        
        return this_latitude, this_longitude
    except Exception as e:
        print(f"Error retrieving latitude or longitude: {e}")
        return None, None

def get_state_and_subregion_code():
    """
    Get the state and subregion code from the config table.
    """
    try:
        state = get_config_value('state')
        subregion_code = get_config_value('subregion_code')
        return state, subregion_code
    except Exception as e:
        print(f"Error retrieving state or subregion code: {e}")
        return None, None

# get all bird names and the total count of detections for each bird
def get_bird_detections_count(request):
    try:
        # print("get_bird_detections_count view called")
        # Query the Bird model using SQLAlchemy
        birds = Bird.objects.using('birds').all()
        # Initialize a dictionary to count detections for each bird
        detections_count = {}

        for bird in birds:
            # Count the total detections for each bird and track the highest confidence
            if bird.common_name not in detections_count:
                detections_count[bird.common_name] = {
                    'scientific_name': bird.scientific_name,
                    'total_detections': 0,
                    'max_confidence': bird.confidence  # Initialize with the current bird's confidence
                }
            detections_count[bird.common_name]['total_detections'] += 1
            # Update the max confidence if the current bird's confidence is higher
            detections_count[bird.common_name]['max_confidence'] = max(
                detections_count[bird.common_name]['max_confidence'], bird.confidence
            )

        # Serialize the data with unique common names
        bird_detections_count_data = [
            {
                'scientific_name': data['scientific_name'],
                'common_name': common_name,
                'total_detections': data['total_detections'],
                'max_confidence': data['max_confidence'],  
            }
            for common_name, data in detections_count.items()
        ]

        # Return the data as JSON
        # print("bird_detections_count_data: ", bird_detections_count_data)
        return JsonResponse(bird_detections_count_data, safe=False)
    except Exception as e:
        print(f"Error in get_bird_detections_count view: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

def get_wav_spectrogram(request):
    try:
        print("get_wav_spectrogram view called")
        spectrograms = WavSpectrogram.objects.using('birds').all()  # Use Django ORM to fetch spectrograms
        spectrogram_data = [
            {
                'frequencies': spectrogram.frequencies,
                'times': spectrogram.times,
                'spectrogram': spectrogram.spectrogram,
            }
            for spectrogram in spectrograms
        ]
        return JsonResponse(spectrogram_data, safe=False)
    except Exception as e:
        print(f"Error in get_wav_spectrogram view: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

def download_database(request):
    # Path to the database file
    db_path = os.path.join(settings.BASE_DIR, 'BirdNET_UI', 'birds.db')
    
    # Check if the file exists
    if not os.path.exists(db_path):
        raise Http404("Database file not found.")
    
    # Serve the file as a response
    response = FileResponse(open(db_path, 'rb'), content_type='application/x-sqlite3')
    response['Content-Disposition'] = f'attachment; filename="birds.db"'
    return response

def read_ebirds_config(request):
    try:
        print("read_ebirds_config view called")
        configs = eBirdsConfig.objects.using('ebirds').all()  # Fetch all records
        config_list = [
            {
                'state': config.state,
                'subregion_code': config.subregion_code,
                'latitude': config.latitude,
                'longitude': config.longitude,
                'compiled': config.compiled
            }
            for config in configs
        ]
        return JsonResponse(config_list[0], safe=False)  # Return as JSON response
    except Exception as e:
        print(f"Error in read_ebirds_config view: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)
    
def get_all_ebirds(request):
    try:
        ebirds = eBirds.objects.using('ebirds').all()  # Use Django ORM to fetch all eBirds
        ebirds_data = [
            {
                'common_name': ebird.common_name,
                'scientific_name': ebird.scientific_name,
                'species_code': ebird.species_code,
                'rarity': ebird.rarity,
                'image': ebird.image,
            }
            for ebird in ebirds
        ]
        return JsonResponse(ebirds_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_ebirds(request, scientific_name):
    try:
        ebirds = eBirds.objects.using('ebirds').filter(scientific_name__icontains=scientific_name)  # Use Django ORM
        ebirds_data = [
            {
                'common_name': ebird.common_name,
                'scientific_name': ebird.scientific_name,
                'species_code': ebird.species_code,
                'rarity': ebird.rarity,
                'image': ebird.image,
            }
            for ebird in ebirds
        ]
        return JsonResponse(ebirds_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def display_ebirds(request):
    return render(request, 'BirdNET_UI/stats.html')

def get_update_available(request):
    # check if the update is available from start_file_listener.py
    update_available = FileHandler.is_update_available()
    print("update_available: ", update_available)
    return JsonResponse({'update_available': update_available}, safe=False)

def get_all_from_ebirds(request):
    # Use the 'using' method to specify the 'ebirds' database
    ebirds = eBirds.objects.using('ebirds').all()
    ebirds_data = [
        {
            'common_name': ebird.common_name,
            'scientific_name': ebird.scientific_name,
        }
        for ebird in ebirds
    ]
    return JsonResponse(ebirds_data, safe=False)

def compile_ebirds(request):
    print("compile_ebirds... this may take a few minutes")
    latitude, longitude = get_lat_and_long()
    ebird = eBirdStats(latitude=latitude, longitude=longitude)
    print("ebirdstats object created")
    ebird.build_birds_in_region_db()
    print("birds in region db built")
    ebird.set_config_compiled(True)
    print("eBirds database compiled and rarity updated")
    return JsonResponse({'success': 'eBirds database compiled and rarity updated'}, safe=False)

def settings_view(request):
    return render(request, 'BirdNET_UI/settings.html')

def get_config(request):
    config_path = os.path.join(settings.BASE_DIR, 'config.json')
    with open(config_path) as config_file:
        config = json.load(config_file)
    return JsonResponse(config)

@csrf_exempt  # Use with caution; consider using proper CSRF protection
def update_config(request):
    if request.method == 'POST':
        new_config = json.loads(request.body)  # Get new config values from the request
        config_path = os.path.join(settings.BASE_DIR, 'config.json')

        # Load the existing config values
        with open(config_path) as config_file:
            existing_config = json.load(config_file)

        # Update existing config with new values, keeping old fields
        existing_config.update(new_config)

        # Write updated config values to config.json
        with open(config_path, 'w') as config_file:
            json.dump(existing_config, config_file, indent=4)

        return JsonResponse({'status': 'success', 'message': 'Configuration updated.'})

def get_hourly_counts(request, scientific_name):
    # Initialize a list to store counts for each hour (1-24)
    hourly_counts = [0] * 24

    # Fetch all records matching the scientific name
    birds = Bird.objects.using('birds').filter(scientific_name=scientific_name)

    # Iterate over the records and count sightings for each hour
    for bird in birds:
        hour = bird.sighting_time.hour
        hourly_counts[hour] += 1  # Increment the count for the specific hour

    return JsonResponse({'scientific_name': scientific_name, 'hourly_counts': hourly_counts}, safe=False)

def get_weekly_counts(request, scientific_name):
    current_year = datetime.now().year

    # Get counts grouped by year and week
    weekly_counts = (
        Bird.objects.using('birds')
        .filter(scientific_name=scientific_name)
        .annotate(week=TruncWeek('sighting_time'), year=TruncYear('sighting_time'))
        .values('year', 'week')
        .annotate(count=Count('id'))
        .order_by('year', 'week')
    )

    # Initialize a list to store counts for each week
    counts_by_week = [0] * 52  # Assuming 52 weeks in a year

    # Populate the counts_by_week list
    for entry in weekly_counts:
        week_index = entry['week'].isocalendar()[1] - 1  # Get the ISO week number and adjust for zero-based index
        counts_by_week[week_index] += entry['count']

    return JsonResponse(counts_by_week, safe=False)

def get_new_birds(request):
    try:
        # Get the current date and time
        now = datetime.now()

        history_days = get_history_days()
        
        # Get the start of the current year
        start_of_year = datetime(now.year, 1, 1)
        
        # Get the start of the last 7 days
        last_X_days = now - timedelta(days=history_days)
        
        # Get birds seen in the last 7 days
        recent_birds = Bird.objects.using('birds').filter(
            sighting_time__gte=last_X_days
        ).values('common_name', 'scientific_name').annotate(count=Count('id'))
        
        # Get birds seen earlier this year (before the last 7 days)
        earlier_birds = Bird.objects.using('birds').filter(
            sighting_time__gte=start_of_year,
            sighting_time__lt=last_X_days
        ).values_list('common_name', flat=True).distinct()
        
        # Filter for birds that are only in the recent list
        new_birds = [bird for bird in recent_birds if bird['common_name'] not in earlier_birds]
        
        # Get images for the new birds from eBirds database
        result = []
        for bird in new_birds:
            ebird = find_ebird_of_bird(bird)
            if ebird:
                result.append({
                    'common_name': bird['common_name'],
                    'scientific_name': bird['scientific_name'],
                    'count': bird['count'],
                    'image': ebird.image
                })
            else:
                result.append({
                    'common_name': bird['common_name'],
                    'scientific_name': bird['scientific_name'],
                    'count': bird['count'],
                    'image': None
                })
        
        return JsonResponse(result, safe=False)
    except Exception as e:
        print(f"Error in get_new_birds view: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def find_ebird_of_bird(bird):
    ebird_by_scientific_name = eBirds.objects.using('ebirds').filter(scientific_name=bird['scientific_name']).first()
    ebird_by_common_name = eBirds.objects.using('ebirds').filter(common_name=bird['common_name']).first()
    if ebird_by_scientific_name:
        return ebird_by_scientific_name
    elif ebird_by_common_name:
        return ebird_by_common_name
    else:
        return None
    
def find_ebird_by_word(word):
    ebird_by_scientific_name = eBirds.objects.using('ebirds').filter(scientific_name__icontains=word).first()
    ebird_by_common_name = eBirds.objects.using('ebirds').filter(common_name__icontains=word).first()
    
    def shared_letter_count(name, word):
        return len(set(name.lower()) & set(word.lower()))

    # Determine which result is closer to the original search word by most shared letters
    if ebird_by_scientific_name and ebird_by_common_name:
        scientific_name_shared = shared_letter_count(ebird_by_scientific_name.scientific_name, word)
        common_name_shared = shared_letter_count(ebird_by_common_name.common_name, word)
        if scientific_name_shared >= common_name_shared:
            return ebird_by_scientific_name
        else:
            return ebird_by_common_name
    elif ebird_by_scientific_name:
        return ebird_by_scientific_name
    elif ebird_by_common_name:
        return ebird_by_common_name
    else:
        return None

def get_birds_config(request):
    try:
        configs = Config.objects.using('birds').all()
        config_data = {config.key: config.value for config in configs}
        return JsonResponse(config_data)
    except Exception as e:
        print(f"Error in get_birds_config view: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def update_birds_config(request):
    if request.method == 'POST':
        try:
            # Print the raw request body for debugging
            print("Raw request body:", request.body)
            
            # Try to parse the JSON data
            try:
                data = json.loads(request.body)
                print("Parsed JSON data:", data)
            except json.JSONDecodeError as e:
                print("JSON decode error:", e)
                # Try to get form data if JSON parsing fails
                data = request.POST
                print("Form data:", data)
            
            # Check if we have any data
            if not data:
                return JsonResponse({'error': 'No data received'}, status=400)
            
            # Update the config values
            for key, value in data.items():
                print(f"Updating {key} to {value}")
                Config.objects.using('birds').filter(key=key).update(value=value)
            
            # Update Django settings with new values
            if 'confidence_threshold' in data:
                settings.BIRDNET_CONFIDENCE_THRESHOLD = float(data['confidence_threshold'])
            if 'history_days' in data:
                settings.BIRDNET_WEB_HISTORY_DAYS_IN_OBSERVATIONS_TABLE = int(data['history_days'])
            if 'max_frequency' in data:
                settings.SPECTOGRAM_MAX_FREQUENCY = int(data['max_frequency'])
            if 'latitude' in data:
                settings.BIRDNET_LATITUDE = float(data['latitude'])
            if 'longitude' in data:
                settings.BIRDNET_LONGITUDE = float(data['longitude'])
            if 'state' in data:
                settings.BIRDNET_STATE = data['state']
            if 'subregion_code' in data:
                settings.BIRDNET_SUBREGION_CODE = data['subregion_code']

            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error in update_birds_config view: {e}")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def get_observation_stats(request):
    # get the total observations, total species, and total observations over the last historic_days days
    history_days = get_history_days()
    
    confidence_threshold = Config.objects.using('birds').get(key='confidence_threshold').value
    total_observations = Bird.objects.using('birds').filter(confidence__gte=confidence_threshold).count()

    total_species_any_confidence = Bird.objects.using('birds').values('scientific_name').distinct().count()
    total_species = Bird.objects.using('birds').filter(confidence__gte=confidence_threshold).values('scientific_name').distinct().count()
    
    total_observations_last_X_days = Bird.objects.using('birds').filter(sighting_time__gte=datetime.now() - timedelta(days=history_days), confidence__gte=confidence_threshold).count()

    print("total_observations: ", total_observations)
    print("total_species: ", total_species)
    print("total_species_any_confidence: ", total_species_any_confidence)
    return JsonResponse({'confidence_threshold': confidence_threshold, 'history_days': history_days, 'total_observations': total_observations, 'total_species': total_species, 'total_species_any_confidence': total_species_any_confidence, 'total_observations_last_X_days': total_observations_last_X_days}, safe=False)

def get_genus(scientific_name):
    genus = scientific_name.split(' ')[0]
    return genus

def get_family(scientific_name):
    family = scientific_name.split(' ')[-1].split('-')[-1]
    return family


