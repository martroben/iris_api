
import flask
from flask import request, jsonify
app = flask.Flask(__name__)
app.config["DEBUG"] = True


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


    return "Deduplicate and sync iris data to storage from input url"


@app.route('/api/v1/iris/summary', methods=['Get'])
def summarize_iris():
    return "A summary of stored iris data in json or human-readable table format."


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7000)

