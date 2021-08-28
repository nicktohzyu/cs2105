import sys

from typing import List

def repeat(size: int):
    read: int = 0
    while read < size:
        b = sys.stdin.buffer.read1(size-read)
        sys.stdout.buffer.write(b)
        sys.stdout.buffer.flush()
        read += len(b)


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
