import os
import uuid

from flask import Flask, render_template, request, make_response, jsonify

from core.clustering import Clustering
from core.infer import Infer
from core.relationship import Relationship
from core.scanner import TemplateScanner
from core.topology import Topology
from settings import Settings

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'upload/'
app.config['TEMPLATE_SCANNER'] = TemplateScanner(Settings.test_data_path)
app.config['TOPOLOGY'] = Topology(Settings.topology_data_path)
app.config['CLUSTERING'] = Clustering(app.config['TEMPLATE_SCANNER'], app.config['TOPOLOGY'])
app.config['RELATIONSHIP'] = Relationship(app.config['TEMPLATE_SCANNER'], app.config['TOPOLOGY'])
app.config['INFER'] = Infer(app.config['TEMPLATE_SCANNER'], app.config['TOPOLOGY'], app.config['RELATIONSHIP'])


@app.route('/')
def main():
    return render_template('main.html')


@app.route('/locate/', methods=['POST'])
def locate():
    path = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
    request.files.get('file').save(path)

    infer: Infer = app.config['INFER']
    res = infer.infer(path)
    result = {
        'has_root_cause': res[0] is not None,
        'total_time': res[1]
    }
    if res[0] is not None:
        result['node'], total_time, result['message'], result['subgraph'], result['node_to_log_mapping'] = res
        result['subgraph'] = (list(result['subgraph'].nodes), list(result['subgraph'].edges))

    os.remove(path)

    return make_response(jsonify(result))
