import time
import requests
import random

ESP_A_HOST = 'http://192.168.100.126/control'
ESP_B_HOST = 'http://192.168.100.105'

while True:
    previous_time = time.time()
    # requests.post(ESP_A_HOST, json={'angle': 0, 'speed': 0})
    requests.post(ESP_B_HOST, json={'speed': 0, 'avoidance': True})
    print((time.time() - previous_time) * 1000, 'ms')