import select
import socket
import struct

from gate.central_connection import CentralConnection

HEADER_SIZE = struct.calcsize("!I")

class GateServer:
    def __init__(self):
        self.central = CentralConnection()
        self.gate = None
        self.epoll = None
        self.next_request_id = 0
        self.connections = {}  # fd -> socket
        self.buffers = {}  # fd -> outbound data
        self.in_buffers = {}  # fd -> raw bytes received from car
        self.pending_requests = {}  # request_id -> car_fd
        self.central_out_buffer = b""

    def run(self):
        self.central.connect()
        self._create_listening_socket()
        self._register_sockets()
        self._event_loop()

    def _event_loop(self):
        print("Gate server started")

        try:
            while True:
                events = self.epoll.poll()

                for fd, event in events:
                    if fd == self.gate.fileno():
                        self._handle_new_connection(event)

                    elif fd == self.central.fileno():
                        self._handle_central_event(event)

                    elif event & select.EPOLLIN:
                        self._handle_car_read(fd)

                    elif event & select.EPOLLOUT:
                        self._handle_car_write(fd)

                    elif event & select.EPOLLHUP:
                        self._disconnect_client(fd)

        finally:
            self._cleanup()

    def _create_listening_socket(self):
        self.gate = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.gate.bind(("0.0.0.0", 9000))
        self.gate.listen(1000)
        self.gate.setblocking(False)

    def _register_sockets(self):
        self.epoll = select.epoll()
        self.epoll.register(self.central.fileno(), select.EPOLLIN)  # watch for incoming connections
        self.epoll.register(self.gate.fileno(), select.EPOLLIN)

    def _handle_new_connection(self, event):
        conn, addr = self.gate.accept()
        conn.setblocking(False)
        self.connections[conn.fileno()] = conn
        self.buffers[conn.fileno()] = b""
        self.in_buffers[conn.fileno()] = b""
        self.epoll.register(conn.fileno(), select.EPOLLIN)
        print(f"[+] {addr}")

    def _handle_central_event(self, event):
        if event & select.EPOLLIN:
            response = self.central.recv()

            if not response:
                print("Central disconnected")
                return

            # TODO:
            # parse request_id
            # lookup pending_requests
            # put response in correct client's buffer

        elif event & select.EPOLLOUT:

            # TODO:
            # send remaining bytes in central_out_buffer

            pass

    def _handle_car_read(self, fd):
        try:
            data = self.connections[fd].recv(4096)

            if not data:
                self._disconnect_client(fd)
                return

            # Add newly received bytes to this car's buffer
            self.in_buffers[fd] += data

            # We need at least 4 bytes for payload_size
            if len(self.in_buffers[fd]) < HEADER_SIZE:
                return

            # First 4 bytes = payload size
            payload_size = struct.unpack("!I", self.in_buffers[fd][:HEADER_SIZE])[0]

            # Do we already have the entire frame?
            if len(self.in_buffers[fd]) < HEADER_SIZE + payload_size:
                return

            # Extract payload
            payload = self.in_buffers[fd][HEADER_SIZE:HEADER_SIZE + payload_size]

            # Remove processed frame from buffer
            self.in_buffers[fd] = self.in_buffers[fd][HEADER_SIZE + payload_size:]

            # This payload is always EntryRequest from a car
            parking_lot_id, gate_id, wants_handicap, wants_electric = struct.unpack("!IIBB", payload)

            request_id = self.next_request_id
            self.next_request_id += 1

            self.pending_requests[request_id] = fd

            central_payload = struct.pack(
                "!IIIBB",
                request_id,
                parking_lot_id,
                gate_id,
                wants_handicap,
                wants_electric
            )

            central_header = struct.pack("!I", len(central_payload))
            central_message = central_header + central_payload

            self.central.send(central_message)

        except ConnectionResetError:
            self._disconnect_client(fd)
            
    

    def _disconnect_client(self, fd):
        self.epoll.unregister(fd)

        self.connections[fd].close()

        del self.connections[fd]
        del self.buffers[fd]
        del self.in_buffers[fd]

    def _handle_car_write(self, fd):
        sent = self.connections[fd].send(self.buffers[fd])

        self.buffers[fd] = self.buffers[fd][sent:]

        if not self.buffers[fd]:
            self.epoll.modify(fd, select.EPOLLIN)

    def _cleanup(self):
        self.epoll.unregister(self.gate.fileno())
        self.gate.close()
        self.central.close()
        self.epoll.close()