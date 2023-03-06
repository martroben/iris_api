
import logging
import requests
import csv

class Iris:
    def __init__(self, row):
        self.sepal_length = float(row["sepal_length"])
        self.sepal_width = float(row["sepal_width"])
        self.petal_length = float(row["petal_length"])
        self.petal_width = float(row["petal_width"])
        self.species = str(row["species"])


url = "https://gist.githubusercontent.com/curran/a08a1080b88344b0c8a7/" \
           "raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv"

# Download data
response = requests.get(url)
if not response:
    logging.error(f"Data download failed with {response.status_code} ({response.reason}). Url: {url}.")
    exit(1)

# Parse data
data_raw = csv.DictReader(response.text.splitlines())
data = list()
for row in data_raw:
    data += [Iris(row)]