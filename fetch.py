
# standard
import csv
import logging
import requests
import os
import sqlite3
#local
from sql_operations import SqlTableInterface


class Iris:
    """
    Data class for iris data.
    """
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
    species: str

    def __init__(self, row):
        self.sepal_length = float(row["sepal_length"])
        self.sepal_width = float(row["sepal_width"])
        self.petal_length = float(row["petal_length"])
        self.petal_width = float(row["petal_width"])
        self.species = str(row["species"])

    def as_dict(self):
        return {column: self.__getattribute__(column) for column in self.__annotations__}


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

# Create SQL table
sql_connection = sqlite3.connect(sql_path)
sql_iris_table = SqlTableInterface(
    name=sql_table_name,
    columns=Iris.__annotations__,
    connection=sql_connection)

for row in data:
    sql_iris_table.insert(**row.as_dict())
