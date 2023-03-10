
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
    where = arguments.get("where", None)

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


@app.route('/api/v1/iris', methods=['Post'])
def post_iris():
    return "Post iris data in json or csv format"


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


@app.route('/api/v1/iris/sync', methods=['Post'])
def sync_iris():
    """
    :return:
    """
    payload = flask.request.get_json()
    default_iris_data_url = os.getenv("DEFAULT_IRIS_DATA_URL")
    iris_data_url = payload.get("url", default_iris_data_url)
    iris_sql_path = os.getenv("SQL_PATH")
    iris_data_csv = fetch.download_url_data(iris_data_url)
    iris_data = iris.parse_data(iris_data_csv)
    sql_connection = sql_operations.get_connection(iris_sql_path)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    n_rows_inserted = sql_iris_table.insert_unique(data=iris_data)
    print(sql_iris_table.summary())
    return f"{n_rows_inserted} rows inserted."


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
