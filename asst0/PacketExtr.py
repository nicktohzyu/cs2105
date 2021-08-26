import sys

from typing import List

def repeat(size: int):
    i: int = 0
    while i < size:
        b = sys.stdin.buffer.read(1)
        sys.stdout.buffer.write(b)
        i += 1
    sys.stdout.buffer.flush()


while True:
    #each loop processes one packet
    header: bytes = sys.stdin.buffer.read(6)
    if header == b'':
        break

    #scan the size
    sizeBytes: bytes = b''
    while True:
        c: bytes = sys.stdin.buffer.read(1)
        if c == b'B':
            break
        sizeBytes += c
    # print(sizeStr)
    sizeStr = sizeBytes.decode()
    size: int = int(sizeStr)
    # print(size)

    #repeat payload
    repeat(size)
