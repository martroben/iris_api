
# standard
import os
# external
import flask
from flask import request, jsonify
# local
import fetch
import iris
import sql_operations


app = flask.Flask(__name__)
app.config["DEBUG"] = True
os.environ["SQL_PATH"] = ":memory:"


@app.route('/', methods=['GET'])
def home():
    return "<h1>Iris dataset api</h1> \
            <p>Available endpoints:</p>"


@app.route('/api/v1/iris', methods=['GET'])
def get_iris():
    return "Get iris data in json format"


@app.route('/api/v1/iris', methods=['Post'])
def post_iris():
    return "Post iris data in json or csv format"


@app.route('/api/v1/iris', methods=['Delete'])
def delete_iris():
    return "Delete iris data by column name and value"


@app.route('/api/v1/iris/sync', methods=['Post'])
def sync_iris():
    payload = request.get_json()
    iris_data_url = payload["url"]
    iris_sql_path = os.getenv("SQL_PATH")
    iris_data_csv = fetch.download_url_data(iris_data_url)
    iris_data = iris.parse_data(iris_data_csv)
    sql_connection = sql_operations.get_connection(iris_sql_path)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    sql_iris_table.insert_unique(data=iris_data)
    return sql_iris_table.summary()


# local test
iris_data_url = "https://gist.githubusercontent.com/curran/a08a1080b88344b0c8a7/raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv"
iris_sql_path = ":memory:"
iris_data_csv = fetch.download_url_data(iris_data_url)
iris_data = iris.parse_data(iris_data_csv)
sql_connection = sql_operations.get_connection(iris_sql_path)
sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
sql_iris_table.insert_unique(data=iris_data)
sql_iris_table.summary()


@app.route('/api/v1/iris/summary', methods=['Get'])
def summarize_iris():
    return "A summary of stored iris data in json or human-readable table format."


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7000)
