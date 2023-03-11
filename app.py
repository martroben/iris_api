
# standard
import logging
import os
# external
import flask
# local
import fetch
import iris
import sql_operations


app = flask.Flask(__name__)
# app.config["DEBUG"] = True
os.environ["SQL_PATH"] = "./sql_test"
os.environ["DEFAULT_IRIS_DATA_URL"] = "https://gist.githubusercontent.com/curran/" \
                                      "a08a1080b88344b0c8a7/raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv"


@app.route('/', methods=['GET'])
def home():
    info = f"<h1>Iris dataset api</h1>" \
           f"<p>path: ./v1/api</p>" \
           f"<h2>Available endpoints:</h2>" \
           f"<p>GET /iris  - query stored data</p>"
    return info


@app.route('/api/v1/iris', methods=['GET'])
@app.route('/api/v1/iris/all', methods=['GET'])
def get_iris():
    """
    Limited filtering capabilities with where parameter:
    Column names can't include operators (except 'in' without surrounding whitespaces)
    Can't use wildcards
    Multiple statements can be supplied by multiple where parameters
    Multiple statements are always joined by AND
    Limited set of operators: =, !=, <, >, IN
    :return:
    """
    arguments = flask.request.args.to_dict(flat=False)        # Can parse several arguments with same name
    get_all = "iris/all" in str(flask.request.url_rule)       # Determine if the /all endpoint is used
    where = None if get_all else arguments.get("where", None)

    iris_sql_path = os.getenv("SQL_PATH")
    sql_connection = sql_operations.get_connection(iris_sql_path)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    try:
        data = [row.as_dict() for row in sql_iris_table.select_iris(where=where)]
        return flask.jsonify(data)
    except ValueError as value_error:
        error_string = f"Couldn't read data from sql. " \
                       f"{value_error.__class__.__name__} occurred: " \
                       f"{value_error}"
        logging.error(error_string)
        return flask.make_response(error_string, 400)


def parse_post_data(request: flask.request) -> list[iris.Iris]:
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
def post_iris(iris_data: list[iris.Iris] = None, unique: bool = False):
    if not iris_data:                                     # Accept both endpoint requests and calling function manually
        iris_data = parse_post_data(flask.request)
    iris_sql_path = os.getenv("SQL_PATH")
    sql_connection = sql_operations.get_connection(iris_sql_path)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    n_rows_inserted = sql_iris_table.insert_iris(data=iris_data, unique=unique)
    return f"Inserted {n_rows_inserted} rows."


@app.route('/api/v1/iris/unique', methods=['Post'])
def post_iris_unique():
    return post_iris(iris_data=parse_post_data(flask.request), unique=True)


@app.route('/api/v1/iris', methods=['Delete'])
def delete_iris(where: (int | str) = 0):
    """
    Limited filtering capabilities with where parameter:
    Column names can't include operators (except 'in' without surrounding whitespaces)
    Can't use wildcards
    Multiple statements can be supplied by multiple where parameters
    Multiple statements are always joined by AND
    Limited set of operators: =, !=, <, >, IN
    :return:
    """
    arguments = flask.request.args.to_dict(flat=False)        # Can parse several arguments with same name
    where = arguments.get("where", where)

    iris_sql_path = os.getenv("SQL_PATH")
    sql_connection = sql_operations.get_connection(iris_sql_path)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    try:
        n_deleted_rows = sql_iris_table.delete(where=where)
        return f"Deleted {n_deleted_rows} rows"
    except ValueError as value_error:
        error_string = f"Couldn't delete data from sql. " \
                       f"{value_error.__class__.__name__} occurred: " \
                       f"{value_error}"
        logging.error(error_string)
        return flask.make_response(error_string, 400)


@app.route('/api/v1/iris/all', methods=['Delete'])
def delete_iris_all():
    return delete_iris(where="1=1")                 # Run delete with a where statement that is always true


@app.route('/api/v1/iris/sync', methods=['Get'])
def sync_iris():
    """
    :return:
    """
    # Parse url if given
    iris_data_url = flask.request.args.get("url",os.getenv("DEFAULT_IRIS_DATA_URL"))
    print(iris_data_url)
    # Download data
    iris_data_csv = fetch.download_url_data(iris_data_url)
    iris_data = iris.from_csv(iris_data_csv)
    # Insert to sql
    n_rows_inserted = post_iris(iris_data, unique=True)
    return f"Inserted {n_rows_inserted} rows."


@app.route('/api/v1/iris/summary', methods=['Get'])
def summarize_iris():
    iris_sql_path = os.getenv("SQL_PATH")
    sql_connection = sql_operations.get_connection(iris_sql_path)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    json_summary = flask.jsonify(sql_iris_table.summary())
    return json_summary


if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=7000,
        use_reloader=False        # Necessary to function properly on Ubuntu
    )
