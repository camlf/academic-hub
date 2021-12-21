
from IPython.display import display, Javascript
import json
import requests

HUB_BASE_URL = "https://data.academic.osisoft.com"
AUTH_ENDPOINT = f"{HUB_BASE_URL}/auth"


def jss(session_id):
    return f"""
    let t = JSON.stringify(localStorage.getItem("hub_jwt") || '{{"access_token": "none"}}', null, 4);
    const options = {{
        method: 'POST',
        body: JSON.stringify(t),
        headers: {{
            'Content-Type': 'application/json',
            'Authorization': 'Custom {session_id}'
        }},
        // mode: 'no-cors'
    }}; 
    fetch('{AUTH_ENDPOINT}/previous_token', options) 
    .then(function (response) {{
        // console.log(`response: ${{response.text()}}`); 
        console.log('session: {session_id}'); 
        return response.text();
    }})
    .catch(function (error) {{
        console.log("Error: " + error);
    }});
    """


def js(session_id):
    return Javascript(jss(session_id))


def restore_previous_jwt(session_id):
    display(js(session_id))


def save_jwt(good_jwt):
    tjs = f"""
        localStorage.setItem("hub_jwt", JSON.stringify({json.dumps(good_jwt)}));
    """
    display(Javascript(tjs))


def delete_jwt():
    tjs = f"""
        localStorage.removeItem("hub_jwt");
    """
    display(Javascript(tjs))


def get_previous_jwt(session_id):
    r = requests.get(
        f"{AUTH_ENDPOINT}/previous_token",
        headers={"Authorization": f"Custom {session_id}"},
        verify=False,
    )
    if 200 == r.status_code:
        return eval(json.loads(r.text))
    else:
        return {"access_token": "none"}
