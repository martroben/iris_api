
# standard
import os
# external
import flask
# local
import fetch
import iris
import sql_operations


app = flask.Flask(__name__)
app.config["DEBUG"] = True
os.environ["SQL_PATH"] = ":memory:"


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
    Very limited filtering capabilities:
    Column names can't include operators (except 'in' without surrounding whitespaces)
    Can't use wildcards.
    Multiple statements are joined by AND
    Limited set of operators: =, !=, <, >, IN
    :return:
    """
    # Get several arguments with the same name:
    arguments = flask.request.args.to_dict(flat=False)
    param = flask.request.args.getlist('param')
    return "Get iris data in json format"


@app.route('/api/v1/iris', methods=['Post'])
def post_iris():
    return "Post iris data in json or csv format"


@app.route('/api/v1/iris', methods=['Delete'])
def delete_iris():
    return "Delete iris data by column name and value"


@app.route('/api/v1/iris/sync', methods=['Post'])
def sync_iris():
    """
    Sample request:
    curl -X POST http://127.0.0.1:7000/api/v1/iris/sync \
    -H "Content-Type: application/json" \
    -d "{\"url\":\"https://gist.githubusercontent.com \
    /curran/a08a1080b88344b0c8a7/raw/0e7a9b0a5d22642a06d3d5b9bcbad9890c8ee534/iris.csv\"}"
    :return:
    """
    payload = flask.request.get_json()
    iris_data_url = payload["url"]
    iris_sql_path = os.getenv("SQL_PATH")
    iris_data_csv = fetch.download_url_data(iris_data_url)
    iris_data = iris.parse_data(iris_data_csv)
    sql_connection = sql_operations.get_connection(iris_sql_path)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    n_rows_inserted = sql_iris_table.insert_unique(data=iris_data)
    return f"{n_rows_inserted} rows inserted."


@app.route('/api/v1/iris/summary', methods=['Get'])
def summarize_iris():
    iris_sql_path = os.getenv("SQL_PATH")
    sql_connection = sql_operations.get_connection(iris_sql_path)
    sql_iris_table = sql_operations.SqlIrisInterface(connection=sql_connection)
    json_summary = sql_iris_table.summary()
    return json_summary


if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=7000,
        use_reloader=False        # Necessary to function properly on Ubuntu
    )
