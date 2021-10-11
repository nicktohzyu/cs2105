import sys
import time
import zlib
from socket import socket, AF_INET, SOCK_DGRAM

# create UDP client
from typing import List


class AckablePacket:
    payload: str
    sequence_number: int
    acked: bool

    def __init__(self, payload: str, sequence_number: int):
        self.payload = payload
        self.sequence_number = sequence_number
        self.acked = False

    @staticmethod
    def split_into_packets(data: str, PAYLOAD_SIZE: int) -> List:
        sequence_number: int = 0
        start: int = 0
        packets = []
        while start < len(data):
            end: int = start + PAYLOAD_SIZE
            pkt = AckablePacket(data[start:end], sequence_number)
            packets.append(pkt)
            start = end
            sequence_number += 1
        return packets

MAX_DATA_SIZE: int = 50000
def read_all_input() -> str:
    input = ''
    while True:
        line: str = sys.stdin.read(MAX_DATA_SIZE)
        if line == '':
            return input
        input += line


def all_acked(packets: List[AckablePacket]):
    for p in packets:
        if not p.acked:
            return False
    return True


def send_unacked_packets(client_socket: socket, packets: List[AckablePacket]):
    for p in packets:
        if p.acked:
            continue
        # send packet
        send_packet(clientSocket, p)


def send_packet(client_socket: socket, packet: AckablePacket):
    chunk_bytes: bytes = packet.payload.encode()
    sequence_number: int = packet.sequence_number
    sequence_number_bytes: bytes = sequence_number.to_bytes(4, 'big')  # 4 bytes
    checksum: int = zlib.crc32(sequence_number_bytes + chunk_bytes)
    checksum_bytes: bytes = checksum.to_bytes(4, 'big')  # 4 bytes
    udp_payload: bytes = checksum_bytes + sequence_number_bytes + chunk_bytes  # 4+4+50 = 58 bytes
    clientSocket.sendto(udp_payload, (serverHost, serverPort))


def read_all_acks(client_socket: socket, packets: List[AckablePacket]):
    #TODO: consider removing acked packets from packets to be sent
    while True:
        try:
            data: bytes = clientSocket.recv(8)
            checksum_bytes: bytes = data[0:4]  # 4 bytes
            sequence_number_bytes: bytes = data[4:8]  # 4 bytes

            # check
            if zlib.crc32(sequence_number_bytes).to_bytes(4, 'big') != checksum_bytes:
                continue  # ignore this corrupted packet

            sequence_number: int = int.from_bytes(sequence_number_bytes, 'big')
            packets[sequence_number].acked = True

        except BlockingIOError as e:  # no more acks to read
            return


clientHost = 'localhost'
clientPort = 8000
clientSocket: socket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(0.05)
clientSocket.bind((clientHost, clientPort))
clientSocket.setblocking(False)

serverHost = 'localhost'
serverPort = int(sys.argv[1])

data: str = read_all_input()

PAYLOAD_SIZE: int = 50
# SEPARATOR = '_'
packets: List[AckablePacket] = AckablePacket.split_into_packets(data, PAYLOAD_SIZE)
# packets: List[AckablePacket] = [AckablePacket(str[i:i + PAYLOAD_SIZE], i) for i in range(0, len(str), PAYLOAD_SIZE)]
# num_packets = math.ceil(len(data)/PAYLOAD_SIZE)
num_packets = len(packets)

while not all_acked(packets):
    send_unacked_packets(clientSocket, packets)

    SLEEP_MS: int = 50
    time.sleep(SLEEP_MS / 1000)

    read_all_acks(clientSocket, packets)

clientSocket.close()
