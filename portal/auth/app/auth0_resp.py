"""Python Flask WebApp Auth0 integration example
"""
from functools import wraps
import json
from os import environ as env
from werkzeug.exceptions import HTTPException

from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import session
from flask import request
from flask import url_for
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
import responder
import redis

import constants

api = responder.API()

ENV_FILE = find_dotenv()
print("ENV_FILE:", f"{ENV_FILE}")
if ENV_FILE:
    load_dotenv(ENV_FILE)

AUTH0_CALLBACK_URL = env.get(constants.AUTH0_CALLBACK_URL)
AUTH0_CLIENT_ID = env.get(constants.AUTH0_CLIENT_ID)
AUTH0_CLIENT_SECRET = env.get(constants.AUTH0_CLIENT_SECRET)
AUTH0_DOMAIN = env.get(constants.AUTH0_DOMAIN)
AUTH0_BASE_URL = "https://" + AUTH0_DOMAIN
AUTH0_AUDIENCE = env.get(constants.AUTH0_AUDIENCE)
AUTH0_ROLES_KEY = "https://data.academic.osisoft.com/roles"
auth0_debug = int(env.get(constants.AUTH0_DEBUG, 0))
print("debug:", auth0_debug)

app = Flask(__name__, static_url_path="/public", static_folder="./public")
app.secret_key = constants.SECRET_KEY
app.debug = True

app.r = redis.StrictRedis(
    host=env.get("REDIS_HOST"),
    port=6380,
    db=1,
    password=env.get("REDIS_PASSWORD"),
    ssl=True,
)


@app.errorhandler(Exception)
def handle_auth_error(ex):
    response = jsonify(message=str(ex))
    response.status_code = ex.code if isinstance(ex, HTTPException) else 500
    return response


oauth = OAuth(app)

auth0 = oauth.register(
    "auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    api_base_url=AUTH0_BASE_URL,
    access_token_url=AUTH0_BASE_URL + "/oauth/token",
    authorize_url=AUTH0_BASE_URL + "/authorize",
    client_kwargs={
        "scope": "openid profile email app_metadata",
    },
)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if constants.PROFILE_KEY not in session:
            return redirect("/auth/login")
        return f(*args, **kwargs)

    return decorated


# Controllers API
@app.route("/")
def home():
    hub_session_id = request.args.get("hub-id")
    if hub_session_id:
        session["hub-session-id"] = hub_session_id
    return render_template("home.html")


@app.route("/callback")
def callback_handling():
    try:
        token = auth0.authorize_access_token()
    except:
        return "You're not part of the Academic Hub organization", 400

    resp = auth0.get("userinfo")
    userinfo = resp.json()

    session[constants.JWT_PAYLOAD] = userinfo
    session[constants.PROFILE_KEY] = {
        "user_id": userinfo["sub"],
        "name": userinfo["name"],
        "picture": userinfo["picture"],
        # 'app_metadata': userinfo['app_metadata'],
        "token": {"token": token},
    }

    hub_session_id = session.get("hub-session-id")
    if hub_session_id:
        app.r.set("hub:" + hub_session_id, json.dumps(userinfo), 120)
        app.r.set("hub:" + hub_session_id + ":token", str(token), 120)

    return redirect("/auth/dashboard")


@app.route("/login")
def login():
    return auth0.authorize_redirect(
        redirect_uri=AUTH0_CALLBACK_URL
    )  # , audience=AUTH0_AUDIENCE)


@app.route("/logout")
def logout():
    session.clear()
    params = {"returnTo": url_for("home", _external=True), "client_id": AUTH0_CLIENT_ID}
    return redirect(auth0.api_base_url + "/v2/logout?" + urlencode(params))


@app.route("/dashboard")
@requires_auth
def dashboard():
    roles = session[constants.JWT_PAYLOAD][AUTH0_ROLES_KEY]
    pretty_roles = {i: roles[i] for i in roles if "client-" not in i}
    return render_template(
        "dashboard.html",
        userinfo=session[constants.PROFILE_KEY],
        userinfo_pretty=pretty_roles,  # json.dumps(session[constants.JWT_PAYLOAD], indent=4),
        token_pretty=json.dumps(session[constants.PROFILE_KEY]["token"], indent=4),
        debug=auth0_debug,
    )


@app.route("/token")
def return_token():
    hub_session_id = request.headers.get("hub-id")
    if hub_session_id:
        try:
            token = app.r.get("hub:" + hub_session_id)
            if token is None:
                return f'key {"hub:" + hub_session_id} not found"', 400
            else:
                return token.decode("utf-8")
        except:
            return f"not found", 400
    else:
        return "no token", 400


api.mount("/auth", app)

if __name__ == "__main__":
    api.run(address="0.0.0.0", port=3000, debug=True)
