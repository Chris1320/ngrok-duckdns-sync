import sys

from flask import Flask
from flask import abort
from flask import request
from flask import url_for
from flask import redirect
from config_handler.simple import Simple


app = Flask(__name__)
redirect_url = None  # Will be updated when /api/update is contacted.


@app.errorhandler(404)
def error404(e):
    """
    Redirect the request to the actual server because it might be there.
    """

    return redirect(redirect_url + request.full_path if redirect_url is not None else url_for("firstrun"), code=301)


@app.errorhandler(503)
def error503(e):
    return f"""\
<!doctype html>
<html lang=en>
    <head>
        <title>503 Service Unavailable</title>
    </head>
    <body>
        <h1>Service Unavailable</h1>
        <p>The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.</p>

        <h6><a href="{url_for("firstrun")}?admin=true">For the system administrator</a></h6>
    </body>
</html>
"""


@app.route("/favicon.ico")
def favicon():
    return ""  # TODO?


@app.route("/")
def index():
    """
    Redirect the user to the ngrok server. (or any server, really)
    """

    return redirect(redirect_url if redirect_url is not None else url_for("firstrun"), code=301)


@app.route("/firstrun", methods=["GET"])
def firstrun():
    if not request.args.get("admin", False, type=bool):  # FIXME: I don't think it converts the GET param value to bool.
        abort(503)  # Just abort if not admin.

    return """\
<html>
    <head>
        <style type="text/css">
            code {background-color: gray; color: white;}
        </style>
    </head>
    <body>
        <h1>Not Yet Updated</h1>

        <p>The redirect URL hasn't been updated yet.</p>
        <p>Run <code>tunnel.py</code> on your server to start.</p>
    </body>
</html>
"""


@app.route("/api/update")
def update():
    global api_key
    global redirect_url

    request_api_key = request.args.get("key", None, type=str)
    new_redirect_url = request.args.get("redirect_url", None, type=str)
    new_api_key = request.args.get("api_key", None, type=str)

    if request_api_key != api_key:
        abort(401)

    if new_redirect_url is not None:
        redirect_url = new_redirect_url
        print(f"[i] Updated redirect URL to `{redirect_url}`.")
        return "OK"

    elif new_api_key is not None:
        api_key = new_api_key
        print(f"[i] Updated API key.")
        return "OK"

    abort(400)


def main():
    global api_key
    try:
        print("[i] Reading configuration file...")
        config = Simple(sys.argv[1])
        config.load()

    except (IndexError, FileNotFoundError):
        print(f"USAGE: {sys.argv[0]} <config path>")
        sys.exit(1)

    host = config.get("host")
    port = int(config.get("port"))
    api_key = config.get("api_key")

    print(f"Server running on {host}:{port}. Press CTRL+C to exit.")
    app.run(host, port)


if __name__ == "__main__":
    main()
