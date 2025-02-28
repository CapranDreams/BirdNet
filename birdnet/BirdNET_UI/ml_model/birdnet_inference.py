import os
from django.shortcuts import render
from django.conf import settings
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from datetime import datetime

class BirdNetInference:
    def __init__(self):        
        # Load the TensorFlow Lite model using TFSMLayer
        # self.MODEL_PATH = os.path.join(settings.BASE_DIR, 'BirdNET_UI', 'models', 'BirdNET_GLOBAL_6K_V2.4_Model_FP16.tflite')
        # self.AUDIO_FILE_PATH = os.path.join(settings.BASE_DIR, 'BirdNET_UI', 'data', 'wav', '2025-02-02-birdnet-12_56_57.wav')
        self.my_latitude = settings.LATITUDE
        self.my_longitude = settings.LONGITUDE
        self.min_confidence = settings.BIRDNET_CONFIDENCE_THRESHOLD
        self.my_location = settings.LOCATION_NAME

        # Load and initialize the BirdNET-Analyzer models.
        self.analyzer = Analyzer(version=settings.BIRDNET_VERSION)

    def predict(self, audio_path):
        tokens = audio_path.split('\\')[-1].split('/')[-1].split('.wav')[0].split('~')
        print(tokens)
        year = int(tokens[1])
        month = int(tokens[2])
        day = int(tokens[3])
        hour = int(tokens[4])
        minute = int(tokens[5])
        second = int(tokens[6])
        this_date = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        self.my_location = tokens[7]
        self.my_latitude = tokens[8]
        self.my_longitude = tokens[9]

        recording = Recording(
            self.analyzer,
            audio_path,
            lat=self.my_latitude,
            lon=self.my_longitude,
            date=datetime(year=year, month=month, day=day), 
            min_conf=self.min_confidence,
        )
        recording.analyze()
        
        print("Prediction Time: ", this_date)
        if len(recording.detections) > 0:
            print("Detections: ", recording.detections)
            # print("species: ", recording.detection_list)    # shows common birds for this location and date
            return recording.detections, this_date, self.my_location, self.my_latitude, self.my_longitude
        
        print("No detections")
        return None, None, None, None, None
       

    
