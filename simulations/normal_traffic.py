import requests
import csv
import sys

with open("normal_traffic.csv", newline="") as file:
    reader = csv.DictReader(file)
    count = 0
    for row in reader:       
        count += 1

        response = requests.post("http://mlcasim-api.edwardnafornita.com/output-json", json=row)

        if count == int(sys.argv[1]):
            break
        