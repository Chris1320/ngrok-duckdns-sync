import sys
import socket

from typing import Final
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from config_handler.simple import Simple


class Redirect(SimpleHTTPRequestHandler):
    def do_GET(self):
        print(self.path)

        self.send_response(301)
        self.send_header(
            "Location",
            "%s%s" % (sys.argv[2], self.path)
        )
        self.end_headers()


class Server(TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


def main() -> int:
    try:
        print("[i] Reading configuration file...")
        config = Simple(sys.argv[1])
        config.load()

    except (IndexError, FileNotFoundError):
        print(f"USAGE: {sys.argv[0]} <config path>")
        sys.exit(1)

    host = config.get("host")
    port = int(config.get("port"))
    redirect_url = config.get("redirect_url")

    server_addr = (host, port)
    server = Server(server_addr, Redirect)

    try:
        print(f"Server running on {server_addr[0]}:{server_addr[1]}. Press CTRL+C to exit.")
        server.serve_forever()

    except KeyboardInterrupt:
        print("\n\n[i] Exiting...")

    finally:
        server.server_close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
