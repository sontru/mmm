from http.server import ThreadingHTTPServer
import sys

from .config import DEFAULT_PORT, HOST
from .database import init_database
from .handlers import GameHandler


def run_server(requested_port=DEFAULT_PORT):
    """Start the threaded HTTP server on the first available port."""
    init_database()
    for port in range(requested_port, requested_port + 20):
        try:
            server = ThreadingHTTPServer((HOST, port), GameHandler)
        except OSError:
            continue

        print(f"Abbey Island Mystery is running at http://localhost:{port}", flush=True)
        print(f"Admin dashboard is at http://localhost:{port}/admin", flush=True)
        print(f"On your local network, try http://<this-computer-ip>:{port}", flush=True)
        server.serve_forever()
        return

    raise OSError(f"No open port found from {requested_port} to {requested_port + 19}")


def main():
    """Run the module entry point."""
    requested_port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    run_server(requested_port)


if __name__ == "__main__":
    main()
