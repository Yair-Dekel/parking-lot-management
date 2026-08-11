import select
import socket
import struct

from gate.central_connection import CentralConnection

HEADER_SIZE = struct.calcsize("!I")

"""
TCP gateway between simulated cars and the central MainServer.

Responsibilities:
- Accept car connections using epoll.
- Receive framed EntryRequest messages from cars.
- Assign request IDs and map them to car sockets.
- Forward requests to the MainServer.
- Receive MainServer responses and route them back to the correct car.
"""
class GateServer:
    def __init__(self):
        self.central = CentralConnection()
        self.gate = None
        self.epoll = None
        self.next_request_id = 0
        self.connections = {}  # fd -> socket
        self.buffers = {}  # fd -> outbound data waiting to be sent to cars
        self.in_buffers = {}  # fd -> partial/incomplete framed data received from cars
        self.pending_requests = {}  # request_id -> originating car fd
        self.central_out_buffer = b""


    """
    Initializes all Gate communication components and starts the event loop.
    """
    def run(self):
        self.central.connect()
        self._create_listening_socket()
        self._register_sockets()
        self._event_loop()


    """
    Main epoll loop.

    Dispatches events from:
    - the Gate listening socket
    - the persistent MainServer connection
    - connected car sockets
    """
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


    """
    Creates the non-blocking TCP listening socket used by cars to connect
    to this Gate.
    """
    def _create_listening_socket(self):
        self.gate = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gate.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.gate.bind(("0.0.0.0", 9000))
        self.gate.listen(1000)
        self.gate.setblocking(False)


    """
    Creates the epoll instance and registers the initial sockets:
    the MainServer connection and the Gate listening socket.
    """
    def _register_sockets(self):
        self.epoll = select.epoll()
        self.epoll.register(self.central.fileno(), select.EPOLLIN)  # watch for incoming connections
        self.epoll.register(self.gate.fileno(), select.EPOLLIN)


    """
    Accepts a new car connection, initializes its buffers, and registers its socket with epoll.
    """
    def _handle_new_connection(self):
        conn, addr = self.gate.accept()
        conn.setblocking(False)
        self.connections[conn.fileno()] = conn
        self.buffers[conn.fileno()] = b""
        self.in_buffers[conn.fileno()] = b""
        self.epoll.register(conn.fileno(), select.EPOLLIN)
        print(f"[+] {addr}")


    """
    Handles events on the persistent MainServer connection.

    Incoming responses will eventually be matched to cars using request_id.
    """
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


    """
    Reads framed EntryRequest data from a car socket.

    The car frame format is [payload_size][EntryRequest payload]

    The EntryRequest payload contains: parking_lot_id, gate_id, wants_handicap, wants_electric

    Once a full frame is available, the Gate:
    - deserializes the EntryRequest,
    - generates a unique request_id,
    - maps request_id to the originating car fd,
    - builds a new framed request for the MainServer,
    - forwards it to the MainServer.
    """
    def _handle_car_read(self, fd):
        try:
            data = self.connections[fd].recv(4096)

            if not data:
                self._disconnect_client(fd)
                return

            # Preserve partial TCP data until a complete application frame is available.
            self.in_buffers[fd] += data

            # The frame header is a 4-byte unsigned payload length
            if len(self.in_buffers[fd]) < HEADER_SIZE:
                return

            # First 4 bytes = payload size
            payload_size = struct.unpack("!I", self.in_buffers[fd][:HEADER_SIZE])[0]

            # TCP may split a frame across multiple recv() calls
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

            self.pending_requests[request_id] = fd # Used later to route the MainServer response back to this car

            central_payload = struct.pack(
                "!IIIBB",
                request_id,
                parking_lot_id,
                gate_id,
                wants_handicap,
                wants_electric
            )

            central_header = struct.pack("!I", len(central_payload))
            central_message = central_header + central_payload # Gate -> MainServer frame: [payload_size][request_id + EntryRequest fields]

            self.central.send(central_message)

        except ConnectionResetError:
            self._disconnect_client(fd)
            
    
    """
    Removes a disconnected car from epoll, closes its socket,
    and deletes all buffers associated with that file descriptor.
    """
    def _disconnect_client(self, fd):
        self.epoll.unregister(fd)

        self.connections[fd].close()

        del self.connections[fd]
        del self.buffers[fd]
        del self.in_buffers[fd]

    """
    Sends buffered response data to a car.

    Handles partial socket writes by keeping unsent bytes in the buffer.
    """
    def _handle_car_write(self, fd):
        sent = self.connections[fd].send(self.buffers[fd])

        self.buffers[fd] = self.buffers[fd][sent:]

        if not self.buffers[fd]:
            self.epoll.modify(fd, select.EPOLLIN)


    """
    Releases the Gate listening socket, MainServer connection and epoll resources.
    """
    def _cleanup(self):
        self.epoll.unregister(self.gate.fileno())
        self.gate.close()
        self.central.close()
        self.epoll.close()