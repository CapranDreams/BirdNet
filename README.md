# BirdNet
Customized BirdNET
This uses the [Cornell BirdNET](https://birdnet.cornell.edu/) sound identification machine learning model to detect birds in your backyard from a microphone. It also uses the [Cornell eBird API](https://ebird.org/home) for getting rarity of birds in your area.

Shows which birds have been around recently, and at what times they are making noise. You can also see a spectrogram showing the frequency vs time plot of the bird call itself below and an analysis of it below that for the last 30 second recording. You can also download the full database if you want to process these results in other ways or to prepare your own plots. Settings for the site can be adjusted in the settings page if you want to change windowing or thresholds for detection.
![image](https://github.com/user-attachments/assets/5b568b94-533a-430e-bc11-7e2b21041f34)
![image](https://github.com/user-attachments/assets/3b08399e-a358-4071-9164-7042bec3adf5)


Edit settings for the birdnet. Adjust the confidence threshold for displaying results, and the confidence threshold for logging to the database seperately. This allows you to adjust the threshold for displaying results at any point. Adjust the 'history days' to change how much data the tables give you information about.
![image](https://github.com/user-attachments/assets/e69d7877-d19a-4a40-82a1-3fe4d5ca5c47)


See which birds from your area have been recorded in your yard. Generates cards for all birds detected in your region in the last 30 days (or if you have counts) based on the eBirds API. Shows your sighting counts and the highest confidence recording for each bird. You can sort by popularity, rarity, common name, or scientific name. Or you can search for a particular bird if you want to know if you have seen them recently.
![image](https://github.com/user-attachments/assets/ef2b8045-dbde-4351-8d39-1bf4ff78c897)
![image](https://github.com/user-attachments/assets/ca67980d-a2ce-46c7-af5d-fb788a46aaa6)


See when certain birds are out with graphs showing sightings per hour of the day and per week of the year. This could help you figure out when to go outside and look for a particular bird. For example, the owl comes out in my yard at midnight every night for a couple hours. Or the bald eagle comes in at 1pm every day.
![image](https://github.com/user-attachments/assets/4c3b9094-9503-4002-b8db-24012c6a6124)
![image](https://github.com/user-attachments/assets/293f98c4-98c2-4cfc-b9dd-9fb046395e56)
![image](https://github.com/user-attachments/assets/56ff9003-a1b4-49f8-a0a9-4176749b4782)


# Setup
- Clone this repository
- Install dependencies
- Create database using command:
  * python manage.py create_tables
    * Update your latitude, longitude, state, and substate code (if you don't know this last one, follow the instructions in the jupyter notebook using the method below)
  * Or manually following the instructions in examples/create_tables.py
    * Configure your latitude, longitude, state, and substate code (if you don't know this last one, follow the instructions in the jupyter notebook)
    * This notebook should only be run once or it will create extra config entries. This likely does not break anything, but should be avoided. You can always delete the entire birds.db or ebirds.db file and create a new one (you will lose any birds added).
- Adjust one file in particular so that it points to the right served IP
  * birdnet/BirdNET_UI/static/js/birds.js : line 1
  * const socket = new WebSocket('ws://localhost:8151/ws/birds/');  // Adjust the URL as necessary
  * Adjust this line by replacing localhost with your server's local IP address (192.168.0.XXX)
- You may need to open up firewall options. Do not open your ports up to the entire world, just your local network!
- If you want to clone an existing BirdNetPi database into here:
  * Follow the instructions in examples/import_birdnetpi_db.ipynb
