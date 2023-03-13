
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
import log
import sql_operations

# Uncomment for testing on host (not Docker)
# os.environ["SQL_PATH"] = "./iris.sql"
# os.environ["DEFAULT_IRIS_DATA_URL"] = "https://gist.githubusercontent.com/curran/" \
#                                       "a08a1080b88344b0c8a7/raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv"
# os.environ["LOG_LEVEL"] = "INFO"
# os.environ["LOG_NAME"] = "iris"
# os.environ["API_PORT"] = "7000"
# os.environ["API_HOST"] = "0.0.0.0"
# os.environ["FLASK_DEBUG_MODE"] = "0"
# os.environ["LOG_INDICATOR"] = "rabbitofcaerbannog"


###############
# Set logging #
###############

log_name = os.getenv("LOG_NAME", "root")  # Use only names that can also be folder names.
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_indicator = os.environ.get("LOG_INDICATOR", str())  # Unique sequence to indicate where to cut syslog entries.
logger = log.get_logger(log_name, log_level, log_indicator)


###############
# Setup Flask #
###############

app = flask.Flask(__name__)

# Add handlers to Flask loggers
# Flask uses a logger by the app name and a inherited 'werkzeug' logger
flask_logs = [app.name, "werkzeug"]
for log_name in flask_logs:
    app_logger = logging.getLogger(log_name)
    app_logger.handlers.clear()
    app_logger.addHandler(logger.handlers[0])
    app_logger.setLevel(log_level)

app.config["DEBUG"] = bool(int(os.environ.get("FLASK_DEBUG_MODE", 0)))


###################
# Flask endpoints #
###################

@app.route('/', methods=['GET'])
def home():
    """Root endpoint with api info."""
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
        log_entry = log.SqlConnectError(database_error, database_path=iris_sql_path)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 500)


def parse_post_data(request: flask.request) -> list[iris.Iris]:
    """
    Parses the payload from a post request, determines whether it's csv or json and
    typecasts it to Iris data type.
    :param request: flask request object
    :return: list of parsed Iris objects
    """
    if request.content_type.lower() == "text/csv":
        payload = request.get_data().decode()
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
        log_entry = log.SqlConnectError(database_error, database_path=iris_sql_path)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 500)
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
        log_entry = log.SqlConnectError(database_error, database_path=iris_sql_path)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 500)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    try:
        n_deleted_rows = sql_iris_table.delete(where=where)
        return f"Deleted {n_deleted_rows} rows"
    except ValueError as value_error:
        log_entry = log.SqlDeleteError(value_error)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 400)


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
        log_entry = log.UrlError(bad_url_error, iris_data_url)
        log_entry.record("ERROR")
        return flask.make_response(log_entry.short, 500)


@app.route('/api/v1/iris/summary', methods=['Get'])
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
