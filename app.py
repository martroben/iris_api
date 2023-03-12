
# standard
import logging
import os
from requests.exceptions import MissingSchema, ConnectionError
import sqlite3
# external
import flask
# local
import general
import iris
import sql_operations


# os.environ["SQL_PATH"] = "./iris.sql"
# os.environ["DEFAULT_IRIS_DATA_URL"] = "https://gist.githubusercontent.com/curran/" \
#                                       "a08a1080b88344b0c8a7/raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv"
# os.environ["LOG_LEVEL"] = "DEBUG"
# os.environ["LOG_NAME"] = "iris"
# os.environ["API_PORT"] = 7000

###############
# Set logging #
###############

log_name = os.getenv("LOG_NAME", "root")
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

logger = logging.getLogger(log_name)
logger.setLevel(log_level)
handler = logging.StreamHandler()                   # Direct logs to stdout
formatter = logging.Formatter(
    fmt=f"{{asctime}} | {{funcName}} | {{levelname}}: {{message}}",
    datefmt="%m/%d/%Y %H:%M:%S",
    style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)


###################
# Flask endpoints #
###################

app = flask.Flask(__name__)
# app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    info = """\
    <h1>Iris dataset api</h1>
    <p>path: ./v1/api</p>
    </br>
    <h2>Available endpoints:</h2>
    <h3>GET:</h3>
    <p>/iris &emsp; - query stored data. Use 'where' parameter for filtering.</p>
    <p>/iris/all &emsp; - get all stored data.</p>
    <p>/iris/sync &emsp; - insert iris csv from url specified in 'url' parameter. Inserts only non-existing rows.</p>
    <p>/iris/summary &emsp; - get per-column summary of stored data.</p>
    </br>
    <h3>POST:</h3>
    <p>/iris &emsp; - add data. Use Content-Type "text/csv" for csv, otherwise "application/json".</p>
    <p>/iris/unique &emsp; - add data. Adds only rows that don't already exist in storage.</p>
    </br>
    <h3>DELETE:</h3>
    <p>/iris &emsp; - delete stored data. Use 'where' parameter for specifying rows, otherwise no action.</p>
    <p>/iris/all &emsp; - delete all stored data.</p>
    </br>
    <h2>Using 'where' statement:</h2>
    <p>Available operators: =, !=, <, >, IN </p>
    <p>Multiple 'where' statements are joined by AND</p>
    <p>Column names can't contain operators (except 'in' without surrounding whitespaces)</p>
    <p>Values can't contain commas.</p>
    <p>Examples:</p>
    <p>GET /iris?where=petal_length=5.5</p>
    <p>GET /iris?where=petal_width<1</p>
    <p>DELETE /iris?where=species%20IN%20(virginica,setosa)</p>
    <p>GET /iris?where=sepal_width>3.3&where=species%20IN%20(virginica,setosa)</p>
    """
    return info


@app.route('/api/v1/iris', methods=['GET'])
@app.route('/api/v1/iris/all', methods=['GET'])
def get_iris():
    """
    Query stored data. Use 'where' parameter for filtering.
    If no "where" parameter is supplied, returns all data.
    If accessed via /iris/all endpoint, returns all data.
    """
    arguments = flask.request.args.to_dict(flat=False)            # Can parse several arguments with same name
    get_all = "iris/all" in str(flask.request.url_rule).lower()       # Determine if the /all endpoint is used
    where = None if get_all else arguments.get("where", None)

    iris_sql_path = os.getenv("SQL_PATH", "./iris_sql")
    try:
        sql_connection = sql_operations.get_connection(iris_sql_path)
        sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
        data = [row.as_dict() for row in sql_iris_table.select_iris(where=where)]
        return flask.jsonify(data)
    except sqlite3.Error as database_error:
        error_string = f"Error on opening database connection: " \
                       f"{database_error.__class__.__name__} occurred"
        logger.error(f"{error_string}. Database path: {iris_sql_path}. Error: {database_error}")
        return flask.make_response(error_string, 500)


def parse_post_data(request: flask.request) -> list[iris.Iris]:
    """
    Parses the payload from a post request, determines whether it's csv or json and
    typecasts it to Iris data type.
    :param request: flask request object
    :return: list of parsed Iris objects
    """
    content_type = request.headers.get("Content-Type")
    if content_type.lower == "text/csv":
        payload = request.get_data()
        iris_data = iris.from_csv(payload)
    else:
        payload = request.get_json()
        payload = [payload] if not isinstance(payload, list) else payload  # Accept both list and single rows
        iris_data = iris.from_json(payload)
    return iris_data


@app.route('/api/v1/iris', methods=['Post'])
@app.route('/api/v1/iris/unique', methods=['Post'])
def post_iris(iris_data: list[iris.Iris] = None, unique: bool = False):
    """
    Inserts csv or json data to storage, depending on Content-Type header
    :return: String with number of inserted rows.
    """
    if not iris_data:                                                    # Case when endpoint request is used
        unique = "iris/unique" in str(flask.request.url_rule).lower()    # Determine if the /unique endpoint is used
        iris_data = parse_post_data(flask.request)
    iris_sql_path = os.getenv("SQL_PATH", "./iris.sql")
    try:
        sql_connection = sql_operations.get_connection(iris_sql_path)
    except sqlite3.Error as database_error:
        error_string = f"Error on opening database connection: " \
                       f"{database_error.__class__.__name__} occurred"
        logger.error(f"{error_string}. Database path: {iris_sql_path}. Error: {database_error}")
        return flask.make_response(error_string, 500)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    n_rows_inserted = sql_iris_table.insert_iris(data=iris_data, unique=unique)
    return f"Inserted {n_rows_inserted} rows."


@app.route('/api/v1/iris', methods=['Delete'])
@app.route('/api/v1/iris/all', methods=['Delete'])
def delete_iris():
    """
    Delete rows from storage. Rows can be specified by 'where' parameters.
    No action, if no where parameters are supplied.
    If /all endpoint is used, deletes all rows in table.
    :return: String with information about the number of deleted rows.
    """
    delete_all = "iris/all" in str(flask.request.url_rule).lower()  # Determine if the /all endpoint is used
    arguments = flask.request.args.to_dict(flat=False)
    # Value that is always true if delete_all and always false if no where argument is supplied
    where = "1=1" if delete_all else arguments.get("where", "1=0")

    iris_sql_path = os.getenv("SQL_PATH", "./iris.sql")
    try:
        sql_connection = sql_operations.get_connection(iris_sql_path)
    except sqlite3.Error as database_error:
        error_string = f"Error on opening database connection: " \
                       f"{database_error.__class__.__name__} occurred"
        logger.error(f"{error_string}. Database path: {iris_sql_path}. Error: {database_error}")
        return flask.make_response(error_string, 500)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    try:
        n_deleted_rows = sql_iris_table.delete(where=where)
        return f"Deleted {n_deleted_rows} rows"
    except ValueError as value_error:
        error_string = f"Couldn't delete data from sql. " \
                       f"{value_error.__class__.__name__} occurred: " \
                       f"{value_error}"
        logger.error(error_string)
        return flask.make_response(error_string, 400)


@app.route('/api/v1/iris/sync', methods=['Get'])
def sync_iris():
    """
    Sync iris data from 'url' argument. If no 'url' argument, url is pulled from env variable DEFAULT_IRIS_DATA_URL.
    Inserts only non-existing (unique) data.
    :return: String with information about the number of inserted rows.
    """
    # Parse url if given
    iris_data_url = flask.request.args.get("url", os.getenv("DEFAULT_IRIS_DATA_URL"))
    # Download data
    try:
        iris_data_csv = general.download_url_data(iris_data_url)
        iris_data = iris.from_csv(iris_data_csv)
        # Insert to sql
        result_string = post_iris(iris_data, unique=True)
        return result_string
    except (MissingSchema, ConnectionError) as bad_url_error:
        error_string = "Error on downloading Iris data."
        logger.error(f"{error_string} Url: {iris_data_url}. Error: {bad_url_error}")
        return flask.make_response(error_string, 500)


@app.route('/api/v1/iris/summary', methods=['Get'])
def summarize_iris():
    """Get a json summary of the columns and values in stored data."""
    iris_sql_path = os.getenv("SQL_PATH", "./iris.sql")
    try:
        sql_connection = sql_operations.get_connection(iris_sql_path)
    except sqlite3.Error as database_error:
        error_string = f"Error on opening database connection: " \
                       f"{database_error.__class__.__name__} occurred"
        logger.error(f"{error_string}. Database path: {iris_sql_path}. Error: {database_error}")
        return flask.make_response(error_string, 500)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    json_summary = flask.jsonify(sql_iris_table.summary())
    return json_summary


#######
# Run #
#######

if __name__ == '__main__':

    app.run(
        host="0.0.0.0",
        port=os.getenv("API_PORT", 7000),
        use_reloader=False        # Necessary to function properly on Ubuntu
    )
