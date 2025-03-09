from django.core.management.base import BaseCommand
import os
import time
import shutil
from scipy import signal
from scipy.io import wavfile
import numpy as np
from django.conf import settings
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ...models import Bird, BirdNow, WavSpectrogram, eBirds, EBirdsExtra
from ...ml_model.birdnet_inference import BirdNetInference
from ...eBirdStats import eBirdStats
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import websocket
import json
from concurrent.futures import ThreadPoolExecutor
from ...bird_data_scraper import BirdDataScraper

# Initialize BirdNetInference
birdnet_inference = BirdNetInference()
update_available = False

class FileHandler(FileSystemEventHandler):
    def __init__(self, executor):
        self.executor = executor

    def on_created(self, event):
        if event.is_directory:
            return
        # Wait for the file to become available
        if self.wait_for_file_to_stabilize(event.src_path):
            # Submit a new thread to process the file
            self.executor.submit(self.process, event.src_path)

    def wait_for_file_to_stabilize(self, file_path, timeout=10):
        """Wait for the file to stabilize (not changing in size) before processing."""
        start_time = time.time()
        last_size = -1

        while True:
            if not os.path.exists(file_path):
                print(f"File does not exist: {file_path}")
                return False

            current_size = os.path.getsize(file_path)

            if current_size == last_size:
                print(f"File is stable: {file_path}")
                return True

            last_size = current_size

            if time.time() - start_time > timeout:
                print(f"Timeout waiting for file to stabilize: {file_path}")
                return False

            time.sleep(0.5)  # Wait before checking again

    def process(self, file_path):
        try:
            print(f"Processing file: {file_path}")
            update_available = False
            time.sleep(0.2)  # Wait before processing to avoid accessing the file before it's finished transferring
            detections = self.analyze_wav(file_path)
            self.save_spectrogram(file_path)
            self.notify_websocket_directly()

            self.check_for_new_best_recordings(detections, file_path)
            self.delete_wav_file(file_path)
        except Exception as e:
            print(f"Error processing file: {e}")

    def analyze_wav(self, file_path):
        # Add a delay before reading the file to make sure lock removed
        time.sleep(1)  # Wait for 1 second

        try:
            detections, prediction_time, _location_name, _latitude, _longitude = birdnet_inference.predict(file_path)
        except Exception as e:
            print(f"Error during analysis: {e}")
            return

        if detections is None:
            return
        
        self.delete_birds_now_database()
        # iterate through detections and push to database
        print("\n")
        for detection in detections:
            new_bird = Bird(
                scientific_name=detection['scientific_name'],
                common_name=detection['common_name'],
                confidence=float(detection['confidence']),
                sighting_time=prediction_time.replace(tzinfo=None),
                location_name=_location_name,
                latitude=_latitude,
                longitude=_longitude
            )
            new_bird.save(using='birds')
            print(f"New bird saved with ID: {new_bird.id}\n")
            self.push_to_birds_now_database({
                'common_name': detection['common_name'],
                'scientific_name': detection['scientific_name'],
                'confidence': float(detection['confidence']),
                'sighting_time': prediction_time.replace(tzinfo=None),
            })
            
        update_available = True

        return detections

    def check_for_new_best_recordings(self, detections, file_path):
        # Check if any new best recordings are detected
        # if there are no detections, do nothing
        if not detections:
            return

        # if there are multiple detections for the same scientific name, only keep the one with the highest confidence
        detections = self.keep_highest_confidence_detections(detections)

        for detection in detections:
            scientific_name = detection['scientific_name']
            print(f"Processing detection: {scientific_name}") 

            if len(scientific_name) > 0:
                ebird_stats = eBirdStats(latitude=settings.LATITUDE, longitude=settings.LONGITUDE)
                common_name = ebird_stats.get_bird_by_scientific_name(scientific_name).common_name  

                new_filename = f"{scientific_name.replace(' ', '_')}.wav"
                new_filepath = os.path.join(settings.SAVED_RECORDINGS_FOLDER, new_filename)

                # Get the current best recordings from the database
                current_best_recordings = Bird.objects.using('birds').filter(scientific_name=scientific_name).order_by('-confidence').first()
                
                # create new eBirds record if it doesn't exist
                if not eBirds.objects.using('ebirds').filter(scientific_name=scientific_name).exists():
                    species_code = ebird_stats.get_bird_by_scientific_name(scientific_name).species_code
                    img_url = ebird_stats.get_bird_image(scientific_name)
                    rarity = eBirds.objects.using('ebirds').filter(scientific_name=scientific_name).count()
                    ebirds_record = {
                        'common_name': common_name,
                        'scientific_name': scientific_name,
                        'species_code': species_code,
                        'rarity': rarity,
                        'image': img_url,
                    }
                    eBirds.objects.using('ebirds').create(**ebirds_record)



                # create new eBirdsExtra record if it doesn't exist
                if not EBirdsExtra.objects.using('ebirds').filter(scientific_name=scientific_name).exists():    
                    audio_filepath = os.path.relpath(new_filepath, start=settings.STATIC_ROOT)

                    bird_extra = EBirdsExtra(
                        scientific_name=scientific_name,
                        common_name=common_name,
                        best_audio=audio_filepath,
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
                    scraper = BirdDataScraper()
                    bird_data = scraper.get_ebird_extras(common_name)
                    if bird_data.get('audio_url'):
                        bird_extra.ideal_audio = bird_data['audio_url']
                    if bird_data.get('range_map_url'):
                        bird_extra.range_map = bird_data['range_map_url']
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
                    # Be nice to the server
                    time.sleep(1)
                    bird_extra.save(using='ebirds')

            
            # Check if the detection is a new best recording
            if detection['confidence'] > current_best_recordings.confidence or self.no_current_recording(detection['scientific_name']):
                self.copy_recording_to_saved_folder(file_path, new_filepath)
                self.update_best_recording_in_database(detection['scientific_name'])

    def no_current_recording(self, scientific_name):
        # look in file system for a file with the scientific name
        for file in os.listdir(settings.SAVED_RECORDINGS_FOLDER):
            if scientific_name in file:
                return False
        return True

    def copy_recording_to_saved_folder(self, file_path, new_filepath):
        shutil.copy(file_path, new_filepath)

    def update_best_recording_in_database(self, scientific_name):
        new_filename = f"{scientific_name.replace(' ', '_')}.wav"
        # new_filepath = os.path.join(settings.SAVED_RECORDINGS_FOLDER, new_filename)
        best_audio_url = f"static/recordings/{new_filename}"

        EBirdsExtra.objects.using('ebirds').filter(scientific_name=scientific_name).update(best_audio=best_audio_url)

    def keep_highest_confidence_detections(self, detections):
        # if there are multiple detections for the same scientific name, only keep the one with the highest confidence
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)

        # only keep the highest confidence detection for each scientific name
        unique_detections = []
        for detection in detections:
            # the first occurence should be the highest confidence now
            if detection['scientific_name'] not in [d['scientific_name'] for d in unique_detections]:
                unique_detections.append(detection)

        return unique_detections

    def delete_wav_file(self, file_path):
        try:
            os.remove(file_path)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except PermissionError:
            print(f"Permission denied: {file_path}")
        except Exception as e:
            print(f"Error deleting file: {file_path}. Reason: {e}")

    def push_to_birds_database(self, bird):
        # bird = Bird(**results)
        bird.save(using='birds')  # Specify the 'birds' database


    def push_to_birds_now_database(self, results):
        birdnow = BirdNow(**results)
        birdnow.save(using='birds')  # Specify the 'birds' database

    def delete_birds_now_database(self):
        BirdNow.objects.using('birds').all().delete()  # Specify the 'birds' database

    def notify_websocket(self):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "birds",
            {
                "type": "send_bird_update",
                "data": {
                    "update": "True"
                }
            }
        )
        print("WebSocket notification sent. [update available: True]")

    def notify_websocket_directly(self):
        ws = websocket.WebSocket()
        try:
            ws.connect(settings.WEBSOCKET_URL)  
            message = {
                "type": "send_bird_update",
                "data": {
                    "update": "True"
                }
            }
            ws.send(json.dumps(message))
            print("WebSocket message sent directly.")
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")
        finally:
            ws.close()

    def is_update_available(self):
        return update_available

    def save_spectrogram(self, wav_file_path):
        # save the spectrogram data to the database
        sample_rate, samples = wavfile.read(wav_file_path)
        if samples.ndim > 1:  # Check if the audio has more than one channel
            samples = samples[:, 0]  # Use only the first channel
        frequencies, times, spectrogram = signal.spectrogram(samples, sample_rate)
        
        # Filter frequencies to only include those up to the maximum frequency defined in settings
        valid_indices = frequencies <= settings.SPECTOGRAM_MAX_FREQUENCY
        frequencies = frequencies[valid_indices]
        spectrogram = spectrogram[valid_indices, :]

        spectrogramData = WavSpectrogram(
            frequencies=frequencies.tolist(),
            times=times.tolist(),
            spectrogram=spectrogram.tolist(),
        )
        WavSpectrogram.objects.using('birds').all().delete()  # Delete all existing spectrograms
        spectrogramData.save(using='birds')  # Use Django ORM to save the new spectrogram



class Command(BaseCommand):
    help = 'Starts the file listener for new WAV files'
    print("---Starting file listener---")

    def handle(self, *args, **kwargs):
        path = "BirdNET_UI/data/wav"  # Path to watch
        executor = ThreadPoolExecutor(max_workers=4)  # Adjust the number of workers as needed
        event_handler = FileHandler(executor)
        observer = Observer()
        observer.schedule(event_handler, path, recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            observer.stop()
        observer.join() 