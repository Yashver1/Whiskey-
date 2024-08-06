from wsgi_server import WSGIServer
import argparse
import sys
import importlib

SERVER_ADDRESS = (HOST, PORT) = ('', 8888)
SERVER_QUEUE = 1


def make_server(app):
    wsgi = WSGIServer(SERVER_ADDRESS, SERVER_QUEUE)
    wsgi.set_app(app)
    wsgi.serve_loop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Missing App Callable")

    module, var = sys.argv[1].split(":")
    module = importlib.import_module(module)
    app = getattr(module, var)
    make_server(app)
