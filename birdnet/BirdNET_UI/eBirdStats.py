import json
import os
from django.shortcuts import render
from django.conf import settings
from BirdNET_UI.models import eBirds, eBirdsConfig
# from .models import eBirds, eBirdsConfig
# from ..models import eBirds, eBirdsConfig
from django.conf import settings


import requests
EBIRD_API_KEY = settings.EBIRD_API_KEY
# review terms if you want to use the API for commercial purposes
# https://ebird.org/api/keygen
# https://documenter.getpostman.com/view/664302/S1ENwy59
# https://science.ebird.org/en/use-ebird-data


class eBirdStats:
    def __init__(self, latitude, longitude):
        self.api_key = EBIRD_API_KEY

        self.lat = latitude
        self.lon = longitude
        self.state = None
        self.subregion_code = None
        # self.birds_in_region = None

        print("eBirdsConfig: ", eBirdsConfig.objects)

        # self.DATABASE_URL = 'sqlite:///BirdNET_UI/ebirds.db'  # Change this to your actual database URL
        # self.engine = create_engine(self.DATABASE_URL)
        # self.Base = declarative_base()
        # self.Base.metadata.create_all(self.engine)
        # self.Session = sessionmaker(bind=self.engine)

        self.set_location(latitude, longitude)

    def set_location(self, latitude, longitude):
        self.lat = latitude
        self.lon = longitude
        self.state, self.subregion_code = self.get_US_regioncode(self.lat, self.lon)

        print("compiled: ", self.get_config_compiled())
        # check if the ebirds.db config table is true or false for 'compiled'
        # session = self.Session()    
        # config = session.query(eBirdsConfig).first()
        # print(config)
        # session.close()
        # if config and config['compiled'].value == 'false':

        #     # build the birds in region database
        #     print("Building birds in region database")
        #     self.build_birds_in_region_db()
        # else:
        #     print("Birds in region database already built")

    def build_birds_in_region_db(self):
        self.erase_ebirds_database()
        for bird in self.get_all_birds_in_region(self.state):
            scientific_name, common_name, species_code, bird_band = self.get_bird_details(bird)
            if("(hybrid)" in common_name):
                continue;
            img_url = self.get_bird_image(scientific_name)
            rarity = self.sum_recent_observations(self.get_recent_observations(species_code))
            record = {
                'common_name': common_name,
                'scientific_name': scientific_name,
                'species_code': species_code,
                'rarity': rarity,   # actually stores the number of recent observations
                'image': img_url,
            }
            self.push_to_ebirds_database(record)
            self.set_config_compiled(True)


    def push_to_ebirds_database(self, ebird_record):
        # Use Django ORM to save the record
        bird = eBirds(**ebird_record)
        bird.save(using='ebirds')
    def erase_ebirds_database(self):
        # Use Django ORM to delete all records
        eBirds.objects.using('ebirds').all().delete()
    def set_config_compiled(self, compiled):
        # Use Django ORM to update the compiled field
        eBirdsConfig.objects.using('ebirds').update(compiled=compiled)
    def get_config_compiled(self):
        # Use Django ORM to query the eBirdsConfig model
        config = eBirdsConfig.objects.using('ebirds').all()
        print("config: ", config)
        if config:
            return config[0].compiled
        return False



    def get_bird_details(self, bird_code):
        url = f"https://api.ebird.org/v2/ref/taxonomy/ebird?species={bird_code}"
        headers = {"X-eBirdApiToken": self.api_key}
        response = requests.get(url, headers=headers)
        bird_details = response.text.split('\n')[1].split(',')
        scientific_name = bird_details[0]
        common_name = bird_details[1]
        species_code = bird_details[2]
        bird_band = bird_details[5]
        return scientific_name, common_name, species_code, bird_band
    # returns a json of the bird's rarity (% all time sightings in your local region)

    def get_wikipedia_bird_info(self, species_name):
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages|pageprops&format=json&piprop=thumbnail&titles={species_name}&pithumbsize=300&redirects"
        response = requests.get(url)
        return response.json()
    # returns a jpg image of the bird
    def get_bird_image(self, species_name):
        wiki = self.get_wikipedia_bird_info(species_name)
        if 'query' in wiki and 'pages' in wiki['query']:
            page = next(iter(wiki['query']['pages'].values()))
            if 'thumbnail' in page:
                image_url = page['thumbnail']['source']
                return image_url
            else:
                print("No thumbnail found for this species. Substituting default image.")
                return "static/images/bird_not_found.png"
        else:
            print("Invalid response format.")

    # returns a json of all birds in a given region
    def get_all_birds_in_region(self, regionCode):
        url = f"https://api.ebird.org/v2/product/spplist/{regionCode}"
        headers = {"X-eBirdApiToken": self.api_key}
        response = requests.get(url, headers=headers)
        return response.json()
    def get_recent_observations(self, species_code, latitude=None, longitude=None):
        if latitude is None:
            latitude = self.lat
        if longitude is None:
            longitude = self.lon
        url = f"https://api.ebird.org/v2/data/obs/geo/recent/{species_code}?lat={latitude}&lng={longitude}&fmt=json"
        headers = {"X-eBirdApiToken": self.api_key}
        response = requests.get(url, headers=headers)
        return response.json()
    def sum_recent_observations(self, recent_observations):
        # pass in the result of get_recent_observations
        # return the total number of observations by adding all the 'howMany' values
        total = 0
        if isinstance(recent_observations, list):
            for observation in recent_observations:
                total += observation.get('howMany', 0)  # Use get to avoid KeyError
        else:
            print("Recent observations are not in the expected JSON format.")
        return total
    def historical_observations(self, regionCode, y, m, d):
        url = f"https://api.ebird.org/v2/data/obs/{regionCode}/historic/{y}/{m}/{d}&fmt=json"
        headers = {"X-eBirdApiToken": self.api_key}
        response = requests.get(url, headers=headers)

    def get_neighnoring_regions(self, region_code):
        url = f"https://api.ebird.org/v2/ref/adjacent/{region_code}"
        headers = {"X-eBirdApiToken": self.api_key}
        response = requests.get(url, headers=headers)
        return response.json()
    def get_region_details(self, region_code):
        url = f"https://api.ebird.org/v2/ref/region/info/{region_code}"
        headers = {"X-eBirdApiToken": self.api_key}
        response = requests.get(url, headers=headers)
        return response.json()
    def get_subregions(self, regionType, parentRegionCode):
        # The region type: 'country', 'subnational1' or 'subnational2'.
        # The parent region code: 'US' for country, 'US-WI' for subnational1, 'US-WI-27' for subnational2. Or 'world' for world.
        url = f"https://api.ebird.org/v2/ref/region/list/{regionType}/{parentRegionCode}"
        headers = {"X-eBirdApiToken": self.api_key}
        response = requests.get(url, headers=headers)
        return response.json()


        # for now, only works for the US
        return self.get_US_regioncode(latitude, longitude)
    def get_US_regioncode(self, lat, lon):
        # this municipal api is a publicly available, no keys needed afaict
        census_url = str('https://geo.fcc.gov/api/census/area?lat=' +
                        str(lat) +
                        '&lon=' +
                        str(lon) +
                        '&format=json')

        # send out a GET request:
        payload = {}
        get = requests.request("GET", census_url, data=payload)

        # parse the response, all api values are contained in list 'results':
        response = json.loads(get.content)['results'][0]

        state_code = 'US-' + response['state_code']
        subregion_code = state_code + '-' + response['state_fips']

        return state_code, subregion_code

    def get_species_code(self, species_name):
        # query the eBirds database for the species code
        species_name = species_name.replace("_", " ").replace("-", " ")
        species = eBirds.objects.using('ebirds').filter(common_name__icontains=species_name).first()
        # if the species is not found, return None
        if species is None:
            print("species not found")
            return None
        return species.species_code
    
    def get_ebird_sciname(self, species_name):
        # query the eBirds database for the species name
        species = eBirds.objects.using('ebirds').filter(common_name__icontains=species_name).first()
        if species is None:
            print("species not found")
            return None
        return species.scientific_name
        

    def detection_stats(self, species_name):
        # convert species name to species code
        species_code = self.get_species_code(species_name)
        scientific_name = self.get_ebird_sciname(species_name)
        # get the recent observations of a given species
        recent_observations = self.get_recent_observations(species_code)
        # get the total number of observations of a given species in a given region
        total_observations = self.sum_recent_observations(recent_observations)
        # get the bird image
        bird_img = self.get_bird_image(scientific_name)

        print("Bird Stats:")
        print(f"Species: {species_name} ({species_code}) ({scientific_name})")
        print(f"Recent Observations ({self.state}): {total_observations}")
        print(f"Bird Image: {bird_img}")


if __name__ == "__main__":
    ebird = eBirdStats(latitude=45.16520768157281, longitude=-92.74500682708717)

    species_name = "american crow"
    ebird.detection_stats(species_name)






