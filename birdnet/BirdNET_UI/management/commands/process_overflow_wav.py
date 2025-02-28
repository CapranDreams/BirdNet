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
from ...models import Bird, BirdNow, WavSpectrogram, eBirds, eBirdsConfig
from ...ml_model.birdnet_inference import BirdNetInference
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.urls import reverse
from django.test import Client
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import transaction

def process(file_path, detections_batch):
    print(f"Processing file: {file_path}")
    analyze_wav(file_path, detections_batch)
    delete_wav_file(file_path)

def analyze_wav(file_path, detections_batch):
    # Add a delay before reading the file to make sure lock removed
    time.sleep(1)  # Wait for 1 second

    try:
        detections, prediction_time, _location_name, _latitude, _longitude = BirdNetInference().predict(file_path)
    except Exception as e:
        print(f"Error during analysis: {e}")
        return

    if detections is None:
        return
    
    # iterate through detections and push to database
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
        # new_bird.save(using='birds')
        detections_batch.append(new_bird)

def delete_wav_file(file_path):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except PermissionError:
        print(f"Permission denied: {file_path}")
    except Exception as e:
        print(f"Error deleting file: {file_path}. Reason: {e}")

def push_to_birds_database(bird):
    # bird = Bird(**results)
    bird.save(using='birds')  # Specify the 'birds' database


class Command(BaseCommand):
    help = 'Process overflow wav files'
    print("---Starting overflow wav file processor---")

    def handle(self, *args, **kwargs):
        print("Processing overflow wav files")
        # Get all wav files from the overflow directory
        overflow_dir = os.path.join(settings.BASE_DIR, 'BirdNET_UI', 'data', 'overflow')
        wav_files = [os.path.join(overflow_dir, f) for f in os.listdir(overflow_dir) if f.endswith('.wav')]
        detections_batch = []  # Initialize a batch list
        batch_size = 10  # Adjust the batch size as needed

        # Use ThreadPoolExecutor to process files concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:  # Adjust max_workers as needed
            future_to_file = {executor.submit(process, file_path, detections_batch): file_path for file_path in wav_files}

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result[1] is not None:
                        print(f"Successfully processed {result[0]} with detections: {result[1]}")
                    else:
                        print(f"Failed to process {file_path}.")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")


                # Check if the batch size limit is reached
                if len(detections_batch) >= batch_size:
                    # Write the batch to the database
                    with transaction.atomic():
                        for record in detections_batch:
                            push_to_birds_database(record)
                    detections_batch.clear()  # Clear the batch after saving

        # Write any remaining records in the batch
        if detections_batch:
            with transaction.atomic():
                for record in detections_batch:
                    push_to_birds_database(record)