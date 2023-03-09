
# standard
import csv
import logging
import requests
import os
import sqlite3
#local
from sql_operations import SqlIrisInterface
from iris import Iris


# Input
url = "https://gist.githubusercontent.com/curran/a08a1080b88344b0c8a7/" \
           "raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv"
sql_path = ":memory:"


#############
# Functions #
#############

def download_url_data(url: str) -> str:
    response = requests.get(url)
    if not response:
        raise requests.HTTPError(f"Data download failed with {response.status_code} ({response.reason}). Url: {url}.")
    return response.text


def parse_iris_data(csv_data: str) -> list[Iris]:
    data_raw = csv.DictReader(csv_data.splitlines())
    data = list()
    for row in data_raw:
        data += [Iris(row)]
    return data


def get_sql_connection(path: str) -> sqlite3.Connection:
    # Create directories for database if they don't exist
    if path != ":memory:":
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

    connection = sqlite3.connect(path)
    return connection


iris_data_csv = download_url_data(url)
iris_data = parse_iris_data(iris_data_csv)
sql_connection = get_sql_connection(sql_path)
sql_iris_table = SqlIrisInterface(connection=sql_connection)
sql_iris_table.insert_unique(data=iris_data)
print(sql_iris_table.summary())

