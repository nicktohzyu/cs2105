import sys
import zlib
from socket import socket, AF_INET, SOCK_DGRAM
from typing import Dict

SERVER_HOST = "localhost"
serverPort = int(sys.argv[1])
server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind((SERVER_HOST, serverPort))

current_sequence_number = 0
to_print: int = 0
chunks: Dict[int, str] = {}


def send_ack(server_socket: socket, sequence_number: int, client_address):
    sequence_number_bytes: bytes = sequence_number.to_bytes(4, 'big')  # 4 bytes
    checksum: int = zlib.crc32(sequence_number_bytes)
    checksum_bytes: bytes = checksum.to_bytes(4, 'big')  # 4 bytes
    udp_payload: bytes = checksum_bytes + sequence_number_bytes  # 4+4= 58 bytes
    server_socket.sendto(udp_payload, client_address)


while True:
    data, client_address = server_socket.recvfrom(64)  # blocking, expect only 58

    checksum_bytes: bytes = data[0:4]  # 4 bytes
    sequence_number_bytes: bytes = data[4:8]  # 4 bytes
    chunk_bytes: bytes = data[8:]

    # check
    if zlib.crc32(sequence_number_bytes + chunk_bytes).to_bytes(4, 'big') != checksum_bytes:
        continue  # ignore this corrupted packet

    sequence_number: int = int.from_bytes(sequence_number_bytes, 'big')

    # send ack
    send_ack(server_socket, sequence_number, client_address)

    # ignore duplicate
    if sequence_number in chunks:
        continue

    # is new packet 
    # store 
    chunks[sequence_number] = chunk_bytes.decode()
    # print as much as possible
    if sequence_number == to_print:
        while to_print in chunks:
            print(chunks[to_print], end='')
            to_print += 1

