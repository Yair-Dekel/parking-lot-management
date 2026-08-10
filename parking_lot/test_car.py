import socket
import struct

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 9000))

print("Connected to Gate")

parking_lot_id = 3
gate_id = 2
wants_handicap = 1
wants_electric = 0

payload = struct.pack(
    "!IIBB",
    parking_lot_id,
    gate_id,
    wants_handicap,
    wants_electric
)

header = struct.pack("!I", len(payload))

message = header + payload

sock.sendall(message)
sock.close()