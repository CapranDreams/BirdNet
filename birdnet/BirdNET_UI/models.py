from django.db import models

class Bird(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incremented ID
    scientific_name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255)
    confidence = models.FloatField()
    sighting_time = models.DateTimeField()
    location_name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.common_name
    
    class Meta:
        db_table = 'birds'  # Specify the table name as 'birds'
        app_label = 'BirdNET_UI'  # Specify the app label if necessary
        managed = False  # Set to False if the table is managed outside of Django

class BirdNow(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incremented ID
    scientific_name = models.CharField(max_length=255)
    common_name = models.CharField(max_length=255)
    confidence = models.FloatField()
    sighting_time = models.DateTimeField()

    def __str__(self):
        return self.common_name
    
    class Meta:
        db_table = 'birds_now'  # Specify the table name as 'birds_now'
        app_label = 'BirdNET_UI'  # Specify the app label if necessary
        managed = False  # Set to False if the table is managed outside of Django

class WavSpectrogram(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incremented ID
    frequencies = models.JSONField()
    times = models.JSONField()
    spectrogram = models.JSONField()

    class Meta:
        db_table = 'wav_spectrogram'  # Specify the table name as 'wav_spectrogram'
        app_label = 'BirdNET_UI'  # Specify the app label if necessary
        managed = False  # Set to False if the table is managed outside of Django

class eBirds(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incremented ID
    common_name = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255)
    species_code = models.CharField(max_length=50)
    rarity = models.FloatField()
    image = models.CharField(max_length=255)

    def __str__(self):
        return self.common_name
    
    class Meta:
        db_table = 'ebirds'  # Specify the table name if needed
        app_label = 'BirdNET_UI'  # Specify the app label if necessary
        managed = False  # Set to False if the table is managed outside of Django

class eBirdsConfig(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incremented ID
    state = models.CharField(max_length=50)
    subregion_code = models.CharField(max_length=50)
    latitude = models.FloatField()
    longitude = models.FloatField()
    compiled = models.BooleanField()
    
    def __str__(self):
        return self.state
    
    class Meta:
        db_table = 'config'  # Specify the table name as 'config'
        app_label = 'BirdNET_UI'  # Specify the app label if necessary
        managed = False  # Set to False if the table is managed outside of Django

class Config(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.CharField(max_length=255, unique=True)
    value = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    class Meta:
        db_table = 'config'
        app_label = 'BirdNET_UI'
        managed = False
