
# standard
import logging
import os
import requests
from requests.exceptions import MissingSchema, ConnectionError, HTTPError
import sqlite3
# external
import flask
# local
import iris
import log
import sql_operations

# Uncomment for running on host (not Docker)
# os.environ["SQL_PATH"] = "./iris.sql"
# os.environ["DEFAULT_IRIS_DATA_URL"] = "https://gist.githubusercontent.com/curran/" \
#                                       "a08a1080b88344b0c8a7/raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv"
# os.environ["LOG_LEVEL"] = "INFO"
# os.environ["LOGGER_NAME"] = "iris"
# os.environ["API_PORT"] = "7000"
# os.environ["API_HOST"] = "0.0.0.0"
# os.environ["FLASK_DEBUG_MODE"] = "0"
# os.environ["LOG_INDICATOR"] = "rabbitofcaerbannog"


###############
# Set logging #
###############

logger_name = os.getenv("LOGGER_NAME", "root")                         # Use only names that can also be folder names.
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_indicator = os.environ.get("LOG_INDICATOR", str())    # Unique sequence to indicate where to split syslog entries.
logger = log.setup_logger(logger_name, log_level, log_indicator)


###############
# Setup Flask #
###############

app = flask.Flask(__name__)

# Add handlers to Flask loggers
# Flask uses a logger by the app name and an inherited 'werkzeug' logger
flask_loggers = [app.name, "werkzeug"]
for flask_logger_name in flask_loggers:
    flask_logger = logging.getLogger(flask_logger_name)
    flask_logger.handlers.clear()
    flask_logger.addHandler(logger.handlers[0])
    flask_logger.setLevel(log_level)

app.config["DEBUG"] = bool(int(os.environ.get("FLASK_DEBUG_MODE", 0)))


###################
# Flask endpoints #
###################

@app.route("/", methods=["GET"])
def home():
    """Root endpoint with api info."""
    info = """\
    <h1>Iris dataset api</h1>
    <p>path: ./api/v1</p>
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


@app.route("/api/v1/iris", methods=["GET"])
@app.route("/api/v1/iris/all", methods=["GET"])
def get_iris():
    """
    Query stored data. Use "where" parameter for filtering.
    If no "where" parameter is supplied, returns all data.
    If accessed via /iris/all endpoint, returns all data.
    """
    arguments = flask.request.args.to_dict(flat=False)            # Can parse several arguments with same name
    get_all = "iris/all" in str(flask.request.url_rule).lower()       # Determine if the /all endpoint is used
    where = None if get_all else arguments.get("where", None)

    iris_sql_path = os.getenv("SQL_PATH", "/iris_data/iris_sql")
    try:
        sql_connection = sql_operations.get_connection(iris_sql_path)
        sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
        data = [row.as_dict() for row in sql_iris_table.select_iris(where=where)]
        return flask.jsonify(data)
    except sqlite3.Error as database_error:
        log_entry = log.SqlConnectError(database_error, database_path=iris_sql_path)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 500)
    except ValueError as bad_syntax_error:
        log_entry = log.SqlGetError(bad_syntax_error)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 400)


def parse_post_data(request: flask.request) -> list[iris.Iris]:
    """
    Parses the payload from a post request, determines whether it's csv or json.
    Typecasts it to Iris data type
    :param request: flask request object from an incoming post request
    :return: list of parsed Iris objects
    """
    if request.content_type.lower() == "text/csv":
        payload = request.get_data().decode()
        iris_data = iris.from_csv(payload)
    else:
        payload = request.get_json()
        payload = [payload] if not isinstance(payload, list) else payload   # Accepts both list and single rows
        iris_data = iris.from_json(payload)
    return iris_data


@app.route("/api/v1/iris", methods=["POST"])
@app.route("/api/v1/iris/unique", methods=["POST"])
def post_iris(iris_data: list[iris.Iris] = None, unique: bool = False):
    """
    Inserts csv or json data (depending on Content-Type header) to storage
    :return: String with number of inserted rows.
    """
    if not iris_data:                                                    # Case when endpoint request is used
        unique = "iris/unique" in str(flask.request.url_rule).lower()    # Determine if the /unique endpoint is used
        iris_data = parse_post_data(flask.request)
    iris_sql_path = os.getenv("SQL_PATH", "./iris.sql")
    try:
        sql_connection = sql_operations.get_connection(iris_sql_path)
    except sqlite3.Error as database_error:
        log_entry = log.SqlConnectError(database_error, database_path=iris_sql_path)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 500)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    n_rows_inserted = sql_iris_table.insert_iris(data=iris_data, unique=unique)
    return f"Inserted {n_rows_inserted} rows."


@app.route("/api/v1/iris", methods=["Delete"])
@app.route("/api/v1/iris/all", methods=["Delete"])
def delete_iris():
    """
    Delete rows from storage. Rows can be specified by "where" parameters.
    No action, if no "where" parameters are supplied.
    If /all endpoint is used, deletes all rows in table.
    :return: String with information about the number of deleted rows.
    """
    delete_all = "iris/all" in str(flask.request.url_rule).lower()        # Determine if the /all endpoint is used
    arguments = flask.request.args.to_dict(flat=False)
    # Always true if delete_all, always false if no "where" argument
    where = "1=1" if delete_all else arguments.get("where", "1=0")

    iris_sql_path = os.getenv("SQL_PATH", "./iris.sql")
    try:
        sql_connection = sql_operations.get_connection(iris_sql_path)
    except sqlite3.Error as database_error:
        log_entry = log.SqlConnectError(database_error, database_path=iris_sql_path)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 500)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    try:
        n_deleted_rows = sql_iris_table.delete(where=where)
        return f"Deleted {n_deleted_rows} rows"
    except ValueError as bad_syntax_error:
        log_entry = log.SqlDeleteError(bad_syntax_error)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 400)


def download_url_data(url: str) -> str:
    """
    Helper function for downloading text data.
    :param url: Data url
    :return: Data string
    """
    response = requests.get(url)
    if not response:
        raise requests.HTTPError(f"{response.status_code} ({response.reason}). url: {url}.")
    return response.text


@app.route("/api/v1/iris/sync", methods=["GET"])
def sync_iris():
    """
    Sync iris data from url specified in "url" parameter of the GET request.
    If no "url" parameter is included, url from env variable DEFAULT_IRIS_DATA_URL is used.
    Inserts only non-existing (unique) data.
    :return: String with information about the number of inserted rows.
    """
    # Parse url if given
    iris_data_url = flask.request.args.get("url", os.getenv("DEFAULT_IRIS_DATA_URL"))
    try:
        iris_data_csv = download_url_data(iris_data_url)
        iris_data = iris.from_csv(iris_data_csv)
        # Insert to sql
        result_string = post_iris(iris_data, unique=True)
        return result_string
    except (MissingSchema, ConnectionError) as url_error:
        log_entry = log.UrlError(url_error, iris_data_url)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 400)
    except HTTPError as download_error:
        log_entry = log.DownloadError(download_error)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 500)


@app.route("/api/v1/iris/summary", methods=["GET"])
def summarize_iris():
    """Get a json summary of the columns and values in stored data."""
    iris_sql_path = os.getenv("SQL_PATH", "./iris.sql")
    try:
        sql_connection = sql_operations.get_connection(iris_sql_path)
    except sqlite3.Error as database_error:
        log_entry = log.SqlConnectError(database_error, database_path=iris_sql_path)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 500)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    json_summary = flask.jsonify(sql_iris_table.summary())
    return json_summary


#######
# Run #
#######

if __name__ == '__main__':
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = os.getenv("API_PORT", 7000)

    app.run(
        host=api_host,
        port=api_port,
        use_reloader=False        # Necessary to function properly on Ubuntu
    )
