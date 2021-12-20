
from IPython.display import display, Javascript
import json


def jss():
    return """
    let t = JSON.stringify(localStorage.getItem("hub_jwt") || {access_token: "none"}, null, 4);
    fetch(`http://127.0.0.1:5004/?jwt=${t}`, { mode: 'no-cors'})
    .then(function (response) {
        return response.text();
    })
    .catch(function (error) {
        console.log("Error: " + error);
    });
    """


def js():
    return Javascript(jss())


def previous_jwt():
    display(js())


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