from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re


class BirdDataScraper:
    def __init__(self, verbose=False):
        self.base_url = "https://www.allaboutbirds.org"
        self.verbose = verbose

        # Set up Chrome options
        chrome_options = Options()
        # Uncomment the line below to run Chrome in headless mode
        chrome_options.add_argument("--headless")

        # Set up the Selenium WebDriver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def load_webpage(self, url, wait_time=1):
        # Navigate to the desired URL
        self.driver.get(url)

        # Wait for the page to load and perform your scraping logic here
        time.sleep(wait_time)
        
    def get_ideal_audio(self, common_name):
        """Extract the ideal audio URL from the bird page"""
        audio_url = None
        description = None
        tips = None
        find_this_bird = None

        try:
            filtered_name = common_name.replace(" ", "_").replace("'", "")
            bird_page = f"https://www.allaboutbirds.org/guide/{filtered_name}/overview"

            if self.verbose:
                print(f"Bird page [overview]: {bird_page}")

            self.load_webpage(bird_page)

            hero_content = self.driver.find_element(By.CLASS_NAME, "hero-content")
            audio_tag = hero_content.find_element(By.TAG_NAME, "audio")
            audio_url = audio_tag.get_attribute("src")

            if self.verbose:
                print(audio_url)
        except:
            print("No ideal audio found")

        try:
            # description
            
            
            overview_div = self.driver.find_element(By.XPATH, "//div[h2[contains(@class, 'overview')]]")
            p_tags = overview_div.find_elements(By.TAG_NAME, "p")
            largest_inner_html = ""
            for p in p_tags:
                inner_html = p.get_attribute("innerHTML")
                if len(inner_html) > len(largest_inner_html):
                    largest_inner_html = inner_html
            description = largest_inner_html
        except:
            print("No description found")

        try:
            # backyard tips
            tips_div = self.driver.find_element(By.XPATH, "//div[h2[text()='Backyard Tips']]")
            p_tags = tips_div.find_elements(By.TAG_NAME, "p")
            largest_inner_html = ""
            for p in p_tags:
                inner_html = p.get_attribute("innerHTML")
                if len(inner_html) > len(largest_inner_html):
                    largest_inner_html = inner_html
            tips = largest_inner_html
            tips = re.sub(r'<a[^>]*>(.*?)<\/a>', '', tips) # remove the links
        except:
            print("No backyard-tips found")

        try:
            # find this bird
            find_this_bird_div = self.driver.find_element(By.XPATH, "//div[h2[text()='Find This Bird']]")
            p_tags = find_this_bird_div.find_elements(By.TAG_NAME, "p")
            largest_inner_html = ""
            for p in p_tags:
                inner_html = p.get_attribute("innerHTML")
                if len(inner_html) > len(largest_inner_html):
                    largest_inner_html = inner_html
            find_this_bird = largest_inner_html
        except:
            print("No find-this-bird found")
            
        return audio_url, description, tips, find_this_bird
        
    def get_life_story(self, common_name):
        """Extract the life story from the bird page"""
        habitat_value = None
        food_value = None
        nesting_value = None
        behavior_value = None
        conservation_value = None

        try:
            filtered_name = common_name.replace(" ", "_").replace("'", "")
            bird_page = f"https://www.allaboutbirds.org/guide/{filtered_name}/lifehistory"

            if self.verbose:
                print(f"Bird page [overview]: {bird_page}")

            self.load_webpage(bird_page)

            # get thier habitat
            lifehistory_menu = self.driver.find_element(By.CLASS_NAME, "LH-menu")

            habitat = lifehistory_menu.find_element(By.XPATH, ".//li[a[contains(@href, '#habitat')]]")
            habitat_text = habitat.find_element(By.CLASS_NAME, "text-label")
            span_elements = habitat_text.find_elements(By.TAG_NAME, "span")
            if len(span_elements) > 1:
                habitat_value = span_elements[1].get_attribute("innerHTML")

            food = lifehistory_menu.find_element(By.XPATH, ".//li[a[contains(@href, '#food')]]")
            food_text = food.find_element(By.CLASS_NAME, "text-label")
            span_elements = food_text.find_elements(By.TAG_NAME, "span")
            if len(span_elements) > 1:
                food_value = span_elements[1].get_attribute("innerHTML")

            nesting = lifehistory_menu.find_element(By.XPATH, ".//li[a[contains(@href, '#nesting')]]")
            nesting_text = nesting.find_element(By.CLASS_NAME, "text-label")
            span_elements = nesting_text.find_elements(By.TAG_NAME, "span")
            if len(span_elements) > 1:
                nesting_value = span_elements[1].get_attribute("innerHTML")

            behavior = lifehistory_menu.find_element(By.XPATH, ".//li[a[contains(@href, '#behavior')]]")
            behavior_text = behavior.find_element(By.CLASS_NAME, "text-label")
            span_elements = behavior_text.find_elements(By.TAG_NAME, "span")
            if len(span_elements) > 1:
                behavior_value = span_elements[1].get_attribute("innerHTML")

            conservation = lifehistory_menu.find_element(By.XPATH, ".//li[a[contains(@href, '#conservation')]]")
            conservation_text = conservation.find_element(By.CLASS_NAME, "text-label")
            span_elements = conservation_text.find_elements(By.TAG_NAME, "span")
            if len(span_elements) > 1:
                conservation_value = span_elements[1].get_attribute("innerHTML")

            if self.verbose:
                print(habitat_value)
                print(food_value)
                print(nesting_value)
                print(behavior_value)
                print(conservation_value)

        except:
            print(f"Error extracting life story")
        
        return habitat_value, food_value, nesting_value, behavior_value, conservation_value
            
    def get_range_map(self, common_name):
        """
        Extract the range map image URL from the bird page
        
        The range map will come from a webpage of the form:
        https://www.allaboutbirds.org/guide/Snow_Goose/maps-range
        """
        map_url = None
        migration_description = None
        try:
            filtered_name = common_name.replace(" ", "_").replace("'", "")
            bird_page = f"https://www.allaboutbirds.org/guide/{filtered_name}/maps-range"

            if self.verbose:
                print(f"Bird page: {bird_page}")

            self.load_webpage(bird_page)

            # locate the div.main-area
            main_area = self.driver.find_element(By.CLASS_NAME, "main-area")
            
            # now find the img tag
            img_tag = main_area.find_element(By.TAG_NAME, "img")
            map_url = img_tag.get_attribute("src")

            if self.verbose:
                print(map_url)
        except:
            print("No range map found")

        try:
            migration_description_div = self.driver.find_element(By.XPATH, "//div//p[@id='migration-description']").find_element(By.XPATH, "..")

            # Find all <p> tags within the migration description div
            p_tags = migration_description_div.find_elements(By.TAG_NAME, "p")

            # Initialize variables to track the largest innerHTML and corresponding <p> tag
            largest_inner_html = ""

            # Iterate through the <p> tags to find the one with the largest innerHTML
            for p in p_tags:
                inner_html = p.get_attribute("innerHTML")
                print(inner_html)
                if len(inner_html) > len(largest_inner_html):
                    largest_inner_html = inner_html

            # Get the innerHTML of the largest <p> tag
            migration_description = largest_inner_html

            if self.verbose:
                print(migration_description)

        except:
            print("No migration description found")
        
        
        return map_url, migration_description
        
    def get_ebird_extras(self, common_name):
        """
        Extract the eBird extras from the bird page
        """
        record = {}
        range_map_url, migration_description = self.get_range_map(common_name)
        record["range_map_url"] = range_map_url
        record["migration_description"] = migration_description

        habitat_value, food_value, nesting_value, behavior_value, conservation_value = self.get_life_story(common_name)
        record["habitat_value"] = habitat_value
        record["food_value"] = food_value
        record["nesting_value"] = nesting_value
        record["behavior_value"] = behavior_value
        record["conservation_value"] = conservation_value
        
        audio_url, description, tips, find_this_bird = self.get_ideal_audio(common_name)
        record["audio_url"] = audio_url
        record["description"] = description
        record["tips"] = tips
        record["find_this_bird"] = find_this_bird
        
        return record
            
if __name__ == "__main__":
    scraper = BirdDataScraper(verbose=False)
    
    record = scraper.get_ebird_extras("European Starling")
    print(record)

