
# standard
import csv
import logging
import requests
import os
import sqlite3
#local
from sql_operations import SqlIrisInterface
from iris import Iris


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


sql_path = ":memory:"
sql_table_name = "Iris"

# Create directories for database if they don't exist
if sql_path != ":memory:":
    if not os.path.exists(os.path.dirname(sql_path)):
        os.makedirs(os.path.dirname(sql_path))

# Create SQL table and insert data
sql_connection = sqlite3.connect(sql_path)
sql_iris_table = SqlIrisInterface(connection=sql_connection)
sql_iris_table.insert_unique(data=data)


