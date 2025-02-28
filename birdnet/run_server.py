import subprocess
import sys
import os
import threading
from birdnet import settings
import multiprocessing

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def in_venv():
    return sys.prefix != sys.base_prefix

if in_venv():
    print("Running in virtual environment: ", sys.prefix)

# Function to activate the virtual environment and run a command
def run_command(command):
    # Get the path to the Python executable in the virtual environment
    # directory = os.path.dirname(__file__)
    # # get parent directory if detected that this folder is 'birdnet'
    # if os.path.basename(directory) == 'birdnet':
    #     parent_directory = os.path.dirname(directory)
    #     python_executable = os.path.join(parent_directory, 'venv_birdnet', 'Scripts', 'python.exe')  # Adjust for Windows
    # else:
    #     python_executable = os.path.join(directory, 'venv_birdnet', 'Scripts', 'python.exe')  # Adjust for Windows

    # print([python_executable] + command)
    print(["python"] + command)

    # Run the command using the virtual environment's Python
    # subprocess.run([python_executable] + command)
    subprocess.run(["python"] + command)

def start_django_server():
    print(f"Starting birdnet server on {settings.BIRDNET_ADDRESS}:{settings.BIRDNET_PORT}")
    run_command(['manage.py', 'runserver', f'{settings.BIRDNET_ADDRESS}:{settings.BIRDNET_PORT}'])

def start_file_listener():
    run_command(['manage.py', 'start_file_listener'])

def start_websocket():
    print("Starting WebSocket Server")
    # Use Daphne or another ASGI server to start the WebSocket server on a different port
    # CommandLineInterface().run(['daphne', '-b', host_addr, '-p', str(websocket_port), 'SensorDashboardProject.asgi:application'])
    # Use subprocess to run Daphne
    subprocess.run([
        'daphne',
        '-b', settings.BIRDNET_ADDRESS,
        '-p', str(settings.BIRDNET_WS_PORT),
        'birdnet.asgi:application'
    ])

if __name__ == "__main__":
    # Create threads for the Django server and file listener
    server_thread = threading.Thread(target=start_django_server)
    listener_thread = threading.Thread(target=start_file_listener)
    websocket_thread = threading.Thread(target=start_websocket)
    # server_thread = multiprocessing.Process(target=start_django_server)
    # listener_thread = multiprocessing.Process(target=start_file_listener)
    # websocket_thread = multiprocessing.Process(target=start_websocket)

    # Start both threads
    server_thread.start()
    listener_thread.start()
    websocket_thread.start()

    # Optionally, join the threads if you want to wait for them to finish
    server_thread.join()
    listener_thread.join()
    websocket_thread.join()

    

else:
    print("Running in base environment: ", sys.base_prefix)
    print("Restart in venv_birdnet virtual environment")


