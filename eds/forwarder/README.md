# Installation

Run the following in a CMD window:

`pip install -r requirements.txt`

# Run EDS forwarder

`set FLASK_APP=eds_loopback.py`
`python -m flask run`

# Check Forwarder is running

Open a browser tag and go to http://127.0.0.1:5000/

# Testing forwarder 

With Postman, send (POST) any valid OMF message (can be an empty array ('[]' without quote) to endpoint http://127.0.0.1:5000/ingress/messages. 

This message will be forwarded to the endpoint indicated in file `eds_loopback.py`



