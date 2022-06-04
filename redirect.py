from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import socket
import sys

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <port> <redirect url>")
    sys.exit()

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

server_addr = ("", int(sys.argv[1]))
server = Server(server_addr, Redirect)

try:
    print(f"Server running on port {server_addr[1]}. Press CTRL+C to exit twice.")
    server.serve_forever()
except KeyboardInterrupt:
    pass

server.server_close()
