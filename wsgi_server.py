import socket
import os
import io
import sys
import signal
import time


class WSGIServer():
    def __init__(self, server_address, request_queue_size):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(server_address)
        self.socket.listen(request_queue_size)
        host, port = self.socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.port = port
        self.headers_set = []
        signal.signal(signal.SIGCHLD, self.handle_children)

    def set_app(self, app):
        self.app = app

    def handle_children(self, signum, frame):
        try:
            status = os.waitpid(0, os.WNOHANG)
            if status == (0, 0):
                return
        except Exception as e:
            print(e)

    def parse_request(self, request):
        requestObj = {}
        self.request_data = request = request.decode("utf-8")
        requestArr = request.splitlines()
        for line in requestArr:
            print(f">  {line}")
        print("\n")
        request_line, *headers, body = requestArr
        method, path, protocol = request_line.split()

        requestObj["method"] = method
        requestObj["path"] = path
        requestObj["protocol"] = protocol
        requestObj["body"] = body

        return requestObj

    def create_environ(self, request):
        requestObj = self.parse_request(request)
        environ = {}

        environ["wsgi.version"] = (1, 0)
        environ["wsgi.url_scheme"] = "http"
        environ["wsgi.multithread"] = False
        environ["wsgi.multiprocess"] = False
        environ["wsgi.run_once"] = False
        environ["wsgi.error"] = sys.stderr
        environ["wsgi.input"] = io.StringIO(self.request_data)

        environ["SERVER_NAME"] = self.server_name
        environ["SERVER_PORT"] = self.port
        environ["REQUEST_METHOD"] = requestObj["method"]
        environ["PATH_INFO"] = requestObj["path"]
        environ["SERVER_PROTOCOL"] = requestObj["protocol"]

        return environ

    def serve_loop(self):
        while True:
            self.client_connection, self.client_address = self.socket.accept()
            pid = os.fork()
            if pid == 0:
                self.socket.close()
                self.handle_request()
                self.client_connection.close()
                os._exit(0)
            else:
                self.client_connection.close()

    def start_response(self, status, response_headers, exc_info=None):
        self.headers_set[:] = [status, response_headers]

    def handle_request(self):
        if not self.app:
            raise ValueError("No App Callable Set")
        print(f"Request recv by host: {self.client_address}")
        request = self.client_connection.recv(1024)

        environ = self.create_environ(request)
        response = self.app(environ, self.start_response)._next()

        self.finish_response(response)

    def finish_response(self, response):
        try:
            response = response.decode("utf-8")
            responseObj = f"HTTP/1.1 {self.headers_set[0]}\r\n"
            for header in self.headers_set[1]:
                responseObj += f"{header[0]}: {header[1]}\r\n"
            responseObj += f"\r\n{response}"

            for line in responseObj.splitlines():
                print(f"> {line}")
            print("\n")\

            self.client_connection.sendall(responseObj.encode())
            time.sleep(20)
        finally:
            self.client_connection.close()
