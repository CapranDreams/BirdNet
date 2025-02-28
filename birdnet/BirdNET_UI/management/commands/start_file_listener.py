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
from datetime import datetime
# from apscheduler.schedulers.background import BackgroundScheduler
from ...models import Bird, BirdNow, WavSpectrogram, eBirds, eBirdsConfig
from ...ml_model.birdnet_inference import BirdNetInference
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.urls import reverse
from django.test import Client
import websocket
import json
from concurrent.futures import ThreadPoolExecutor
# from consumers import send_bird_update

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
        print(f"Processing file: {file_path}")
        update_available = False
        time.sleep(0.2)  # Wait before processing to avoid accessing the file before it's finished transferring
        self.analyze_wav(file_path)
        self.save_spectrogram(file_path)
        self.notify_websocket_directly()
        self.delete_wav_file(file_path)

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
            ws.connect("ws://localhost:8151/ws/birds/")  
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