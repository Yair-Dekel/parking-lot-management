import socket

CENTRAL_PORT = 5099  # Must match the TCP port used by MainServer
CENTRAL_HOST = "127.0.0.1"


"""
Manages the Gate's persistent TCP connection to the MainServer.
"""
class CentralConnection:
    def __init__(self):
        self.sock = None

    def connect(self):
        """
        Creates the TCP socket and connects the Gate to the MainServer.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((CENTRAL_HOST, CENTRAL_PORT))

    def fileno(self):
        """
        Returns the underlying socket fd for epoll registration.
        """
        return self.sock.fileno()

    def recv(self, size=4096):
        """
        Receives up to `size` bytes from the MainServer.
        """
        return self.sock.recv(size)

    def send(self, data):
        """
        Sends raw bytes to the MainServer.
        """
        return self.sock.send(data)

    def close(self):
        """
        Closes the TCP connection to the MainServer.
        """
        self.sock.close()