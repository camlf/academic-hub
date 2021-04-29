from flask import Flask, request, Response
import requests
import os

EDS_ENDPOINT = os.environ.get("EDS_FORWARD_URL", "http://localhost:5590/api/v1/tenants/default/namespaces/default/omf/")
# EDS_ENDPOINT = "http://httpbin.org/post"

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'EDS Loopback Forwarder v0.9'


@app.route('/ingress/messages', methods=["POST"])    
def send_to_eds(): 
    resp = requests.request(
        method="post", 
        url=EDS_ENDPOINT,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        stream=True)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    return Response(str(resp.json()), resp.status_code, headers)
