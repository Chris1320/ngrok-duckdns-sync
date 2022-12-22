import os
import sys
import time
import socket
from typing import Final
from typing import Optional

import httpx
import colorama
from pyngrok import conf
from pyngrok import ngrok
from pyngrok.exception import PyngrokNgrokError
from config_handler.simple import Simple


SCHEMAS: Final[dict[str, str]] = {
    "http": "http://",
    "https": "https://"
}


def getNgrokPath() -> str | None:
    """
    Get the full path of ngrok binary from PATH. (if it exists)
    """

    path_sep = ';' if os.name == "nt" else ':'
    ngrok_exe = "ngrok.exe" if os.name == "nt" else "ngrok"
    for path in f"{os.getenv('PATH', '')}{path_sep}.".split(path_sep):
        possible_ngrok_path = os.path.join(path, ngrok_exe)
        if os.path.isfile(possible_ngrok_path):
            return possible_ngrok_path


def buildRequest(update_url: str, api_key: str, tunnel_url: str, https: bool = True):
    """
    Create the full URL path to update redirect server's redirect_url value.
    """

    return buildURL(f"{update_url}/api/update/redirect_url?key={api_key}&value={tunnel_url}", https)


def buildURL(url: str, https: bool = True, force_schema: bool = False):
    """
    Add schema to URL.
    """

    schema = SCHEMAS["https"] if https else SCHEMAS["http"]
    if force_schema:
        for existing_schema in SCHEMAS.values():
            if url.startswith(existing_schema):
                return f"{schema}{url.partition(existing_schema)[2]}"

        return f"{schema}{url}"

    return f"{schema}{url}" if not any(map(lambda schema: url.startswith(schema), SCHEMAS.values())) else url


def updateRedirectServer(update_url: str, api_key: str, public_url: str, https: bool = True) -> httpx.Response | int:
    """
    Send a GET request to redirect server.
    """

    try:
        return httpx.get(
            buildRequest(
                update_url,
                api_key,
                public_url,
                https
            )
        )

    except Exception as e:
        print(f"[E] {e}")
        return 1


def updateDuckDNSDomain(
    duckdns_domain: str,
    duckdns_token: str,
    update_url: str,
    server_port: int
) -> bool:
    """
    Update the IP address of DuckDNS domain to <update_url>'s IP address.

    Returns True if success, otherwise False.
    """

    try:
        redirect_server_ipv4 = socket.getaddrinfo(update_url, server_port, socket.AF_INET)[0][4][0]
        return httpx.get(
            f"https://www.duckdns.org/update?domains={duckdns_domain}&token={duckdns_token}&ip={redirect_server_ipv4}"
        ).text == "OK"

    except Exception as e:
        print(f"[E] {e}")
        return False


def checkServer(url: str) -> int:
    """
    Check if the server is up.
    """

    try:
        return httpx.get(url).status_code

    except Exception as e:
        return 1000  # printInfo() considers error codes >= 400 as down.


def printInfo(duckdns_domain: str, update_url: str, update_url_https, server_port: int, ngrok_url: Optional[str] = None):
    """
    Show a simple visualization of the redirects.
    """

    colors = {
        "up": f"{colorama.Fore.LIGHTYELLOW_EX}{colorama.Style.BRIGHT}",
        "down": f"{colorama.Fore.RED}{colorama.Style.BRIGHT}",
        "arrow": f"{colorama.Fore.LIGHTBLACK_EX}",
        "end": colorama.Style.RESET_ALL
    }

    duckdns_url = buildURL(f"{duckdns_domain}.duckdns.org")
    duckdns_up = colors["up"] if checkServer(duckdns_url) < 400 else colors["down"]
    duckdns_info = f"{duckdns_up}{duckdns_url}{colors['end']}"

    redirect_url = buildURL(update_url, update_url_https)
    redirect_up = colors["up"] if checkServer(redirect_url) < 400 else colors["down"]
    redirect_info = f"{redirect_up}{redirect_url}{colors['end']}"

    ngrok_url = "ngrok tunnel" if ngrok_url is None else ngrok_url
    if ngrok_url == "ngrok tunnel":
        ngrok_up = colors["down"]

    else:
        ngrok_up = colors["up"] if checkServer(buildURL(ngrok_url)) < 400 else colors["down"]

    ngrok_info = f"{ngrok_up}{ngrok_url}{colors['end']}"

    server_url = buildURL(f"127.0.0.1:{server_port}", False)
    server_up = colors["up"] if checkServer(server_url) < 400 else colors["down"]
    server_info = f"{server_up}{server_url}{colors['end']}"

    print(
        "{duckdns} {arrow} {redirect} {arrow} {ngrok} {arrow} {server}".format(
            duckdns = duckdns_info,
            redirect = redirect_info,
            ngrok = ngrok_info,
            server = server_info,
            arrow = f"{colors['arrow']}->{colors['end']}",
        )
    )


def main() -> int:
    print("[i] Loading configuration file...")
    config = Simple("config.conf")
    config.load()

    server_port = int(config["server_port"])  # The port of the local server to expose.
    update_url = str(config["update_url"])  # The redirect server.
    update_port = int(config["update_port"])
    api_key = str(config["api_key"])  # redirect server api key
    redirect_url_https = config.get("update_url_https", True)  # Does the redirect server use HTTPS?

    ngrok_path = getNgrokPath() if config.get("ngrok_path", None) is None else config["ngrok_path"]  # The ngrok binary
    ngrok_tunnel_name = config.get("tunnel_name", "redirector tunnel")  # A tunnel name for ngrok
    ngrok_protocol = config["protocol"]  # ngrok tunnel protocol
    ngrok_auth_token = config.get("ngrok_auth_token")  # ngrok API key

    duckdns_domain = config.get("duckdns_domain", None)
    duckdns_token = config.get("duckdns_token", None)

    if api_key == "YOUR_REDIRECT_SERVER_API_KEY_HERE":
        print("[CRITICAL] Change your API key in the configuration file first!")
        print("           `tunnel.py` and `redirector.py` must have the same API key.")
        return 2

    elif ngrok_auth_token == "YOUR_NGROK_AUTH_TOKEN_HERE":
        print("[CRITICAL] Change your API key in the configuration file first!")
        print("           Log in and follow the link below to get your auth token:")
        print("           https://dashboard.ngrok.com/get-started/your-authtoken")
        return 3

    elif update_url == "YOUR_REDIRECT_SERVER_URL_HERE":
        print("[CRITICAL] Set your redirect server URL first!")
        return 4

    print()
    printInfo(duckdns_domain, f"{update_url}:{update_port}", redirect_url_https, server_port)
    print()

    print("[i] Setting up ngrok...")
    ngrok_config = conf.PyngrokConfig()
    ngrok_config.auth_token = ngrok_auth_token
    ngrok_config.monitor_thread = config.get("ngrok_monitor_thread")

    if ngrok_path is None:
        ngrok.install_ngrok(ngrok_config)

    else:
        ngrok_config.ngrok_path = ngrok_path

    print("[i] Starting ngrok...")
    try:
        tunnel = ngrok.connect(
            name=ngrok_tunnel_name,
            addr=server_port,
            proto=ngrok_protocol,
            pyngrok_config=ngrok_config
        )

    except PyngrokNgrokError:
        print("[CRITICAL] Failed to start ngrok!")
        print("           Make sure your auth token is correct.")
        print("           Log in and follow the link below to get your auth token:")
        print("           https://dashboard.ngrok.com/get-started/your-authtoken")
        return 5

    try:
        print(f"[i] ngrok is now serving on {buildURL(tunnel.public_url, True, True)}.")
        print()
        printInfo(duckdns_domain, f"{update_url}:{update_port}", redirect_url_https, server_port, buildURL(tunnel.public_url, True, True))
        print()
        fail_timeout = config.get("redirect_update_fail_retry_timeout", 10)
        success_timeout = config.get("redirect_update_success_timeout", 3600)
        while True:
            print("[i] Updating redirect server...")
            update_request = updateRedirectServer(f"{update_url}:{update_port}", api_key, buildURL(tunnel.public_url, True, True), redirect_url_https)
            update_request_success = update_request.status_code if type(update_request) is httpx.Response else update_request
            if update_request_success != 200:
                print(f"[E] Failed to update redirect server. Retrying in {fail_timeout} seconds.")
                time.sleep(fail_timeout)
                continue

            print("[i] Redirect server updated! You can now visit your server on port {port} using the URL {url}. ({update})".format(
                port = f"{colorama.Fore.LIGHTYELLOW_EX}{server_port}{colorama.Style.RESET_ALL}",
                url = f"{colorama.Fore.LIGHTYELLOW_EX}{update_url}:{update_port}{colorama.Style.RESET_ALL}",
                update = f"update in {success_timeout}s"
            ))

            if duckdns_domain is not None:
                print("[i] Updating DuckDNS domain...")
                if not updateDuckDNSDomain(duckdns_domain, duckdns_token, update_url, update_port):
                    print(f"[E] Failed to update DuckDNS domain. Retrying in {fail_timeout} seconds.")
                    time.sleep(fail_timeout)
                    continue

                else:
                    print("[i] DuckDNS domain updated! You can now visit your server on port {port} using the URL {url}. ({update})".format(
                        port = f"{colorama.Fore.LIGHTYELLOW_EX}{server_port}{colorama.Style.RESET_ALL}",
                        url = f"{colorama.Fore.LIGHTYELLOW_EX}https://{duckdns_domain}.duckdns.org{colorama.Style.RESET_ALL}",
                        update = f"update in {success_timeout}s"
                    ))

            print()
            printInfo(duckdns_domain, f"{update_url}:{update_port}", redirect_url_https, server_port, buildURL(tunnel.public_url, True, True))
            print()
            time.sleep(success_timeout)

    except KeyboardInterrupt:
        print("[i] Updating redirect server...")
        # Set the redirect URL to None to disable the redirect.
        updateRedirectServer(f"{update_url}:{update_port}", api_key, '', redirect_url_https)
        print("[i] Stopping ngrok instance...")
        ngrok.disconnect(tunnel.public_url)
        return 0


if __name__ == "__main__":
    sys.exit(main())
