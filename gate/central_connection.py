import socket

CENTRAL_PORT = 8000
CENTRAL_HOST = "127.0.0.1"


class CentralConnection:
    def __init__(self):
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((CENTRAL_HOST, CENTRAL_PORT))

    def fileno(self):
        return self.sock.fileno()

    def recv(self, size=4096):
        return self.sock.recv(size)

    def send(self, data):
        return self.sock.send(data)

    def close(self):
        self.sock.close()