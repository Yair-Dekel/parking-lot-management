import socket

HOST = "127.0.0.1"
PORT = 8000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Waiting for Gate...")

conn, addr = server.accept()
print(f"Connected: {addr}")

while True:
    data = conn.recv(4096)
    if not data:
        break

    print("Received:", data.decode())

    message = input("Reply: ")
    conn.sendall(message.encode())