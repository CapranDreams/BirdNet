from django.core.management.base import BaseCommand
import sqlite3
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Create all required database tables for BirdNET_UI'

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating database tables for BirdNET_UI...")
        
        # Create birds.db tables
        self.create_birds_db_tables()
        
        # Create ebirds.db tables
        self.create_ebirds_db_tables()
        
        self.stdout.write(self.style.SUCCESS("All tables created successfully!"))
    
    def create_birds_db_tables(self):
        birds_db_path = os.path.join(settings.BASE_DIR, 'BirdNET_UI', 'birds.db')
        self.stdout.write(f"Creating tables in {birds_db_path}")
        
        conn = sqlite3.connect(birds_db_path)
        cursor = conn.cursor()
        
        # Create birds table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS birds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT NOT NULL,
            common_name TEXT NOT NULL,
            confidence REAL NOT NULL,
            sighting_time TIMESTAMP NOT NULL,
            location_name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        )
        ''')
        
        # Create birds_now table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS birds_now (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT NOT NULL,
            common_name TEXT NOT NULL,
            confidence REAL NOT NULL,
            sighting_time TIMESTAMP NOT NULL
        )
        ''')
        
        # Create wav_spectrogram table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS wav_spectrogram (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frequencies TEXT NOT NULL,
            times TEXT NOT NULL,
            spectrogram TEXT NOT NULL
        )
        ''')
        
        # Create config table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
        ''')
        
        # Insert default config values if they don't exist
        default_configs = [
            ('confidence_threshold', '0.7'),
            ('history_days', '7'),
            ('max_frequency', '12000'),
            ('latitude', '0'),
            ('longitude', '0'),
            ('state', ''),
            ('subregion_code', ''),
            ('confidence_threshold_for_add_to_db', '0.4')
        ]
        
        for key, value in default_configs:
            cursor.execute('''
            INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)
            ''', (key, value))
        
        conn.commit()
        conn.close()
        self.stdout.write(self.style.SUCCESS("Birds database tables created successfully!"))
    
    def create_ebirds_db_tables(self):
        ebirds_db_path = os.path.join(settings.BASE_DIR, 'BirdNET_UI', 'ebirds.db')
        self.stdout.write(f"Creating tables in {ebirds_db_path}")
        
        conn = sqlite3.connect(ebirds_db_path)
        cursor = conn.cursor()
        
        # Create ebirds table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ebirds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            common_name TEXT NOT NULL,
            scientific_name TEXT NOT NULL,
            species_code TEXT NOT NULL,
            rarity REAL NOT NULL,
            image TEXT
        )
        ''')
        
        # Create ebirds_world table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ebirds_world (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT NOT NULL,
            common_name TEXT NOT NULL,
            species_code TEXT NOT NULL
        )
        ''')
        
        # Create config table for ebirds
        # cursor.execute('''
        # CREATE TABLE IF NOT EXISTS config (
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     state TEXT,
        #     subregion_code TEXT,
        #     latitude REAL,
        #     longitude REAL,
        #     compiled BOOLEAN DEFAULT 0
        # )
        # ''')
        
        # Insert default config if it doesn't exist
        cursor.execute('''
        INSERT OR IGNORE INTO config (id, state, subregion_code, latitude, longitude, compiled)
        VALUES (1, '', '', 0, 0, 0)
        ''')
        
        # Create ebirds_extra table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ebirds_extra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT UNIQUE NOT NULL,
            common_name TEXT NOT NULL,
            best_audio TEXT,
            ideal_audio TEXT,
            range_map TEXT,
            migration_description TEXT,
            description TEXT,
            tips TEXT,
            find_this_bird TEXT,
            habitat_value TEXT,
            food_value TEXT,
            nesting_value TEXT,
            behavior_value TEXT,
            conservation_value TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        self.stdout.write(self.style.SUCCESS("eBirds database tables created successfully!")) 