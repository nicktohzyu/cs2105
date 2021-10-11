import sys
import socket
from typing import Dict, List, Optional, Any

IP_ADDR: str = "127.0.0.1"
BUFFER_SIZE: int = 4096


class ResponseFormer(object):
    @staticmethod
    def resp(value: bytes) -> bytes:
        return f'200 OK content-length {len(value)}  '.encode() + value


class KVStore(object):
    store: Dict[str, bytes]

    def __init__(self):
        self.store = {}

    def get(self, key) -> bytes:
        value = self.store.get(key)

        if value is None:
            return b'404 NotFound  '

        return ResponseFormer.resp(value)

    def post(self, key: str, val: bytes) -> bytes:
        self.store[key] = val
        return b'200 OK  '

    def delete(self, key) -> bytes:
        if key in self.store:
            value = self.store.get(key)
            del self.store[key]
            return ResponseFormer.resp(value)
        return b'404 NotFound  '


class Counter(object):
    store: Dict[bytes, int]

    def __init__(self):
        self.store = {}

    def get(self, key: bytes) -> bytes:
        value: Optional[int] = self.store.get(key)

        if value is None:
            value = 0

        s: bytes = str(value).encode()
        return ResponseFormer.resp(s)

    def post(self, key: bytes) -> bytes:
        value: Optional[int] = self.store.get(key)

        if value is None:
            value = 0
            self.store[key] = 1
        else:
            self.store[key] += 1
        s: bytes = str(value).encode()
        return b'200 OK  '


class WebServer(object):
    store: KVStore
    counter: Counter
    server_socket: socket
    port: int

    def __init__(self, port_: int):
        self.port = port_
        self.store = KVStore()
        self.counter = Counter()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((IP_ADDR, self.port))
        self.server_socket.listen()  # listen(1)?

        while True:
            try:
                conn: socket
                conn, addr = self.server_socket.accept()
                # print("Address:", addr)
                self.handle_connection(conn)
                # print("End conn", addr)
            except (KeyboardInterrupt, SystemExit):
                break
        self.shutdown()

    def shutdown(self):
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()
        exit(0)

    def handle_connection(self, conn: socket):
        data = b""
        receiving_data = True
        while True:
            if receiving_data:
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    receiving_data = False
                else:
                    data += chunk

            if not receiving_data and not data:
                return

            while data:
                # Each time data is received, attempt a parse
                eor: int
                request, eor = self.parse_request(data)
                # check if the accumulated data sufficient to represent a request
                if not request:  # instead check eor == -1?
                    break

                # print("Request: ", request)
                response = self.handle_request(request)
                response_s = response
                # response_s = HTTPResponse.construct_response(response)
                # print("Responding with: ", response_s)
                conn.sendall(response_s)
                data = data[eor:]

    @staticmethod
    def parse_request(s: bytes) -> (Dict[str, Any], int):
        request: Dict[str] = {}
        end_of_req: int
        separation_idx: int = s.find(b"  ")
        if separation_idx == -1:
            return request, -1

        headers: List[str] = s[:separation_idx].decode("ascii").split()
        request['method'] = headers[0].upper()  # e.g. GET, case-insensitive
        request['path'] = headers[1]  # e.g. /key/1, case-sensitive

        # Rest is header key value pairs
        for idx in range(2, len(headers), 2):
            k = headers[idx].lower()
            v = headers[idx + 1]
            request[k] = v

        if 'content-length' in request:  # if there's content, truncate to content-length
            start = separation_idx + 2  # after two spaces
            length = int(request['content-length'])
            end = start + length

            if len(s) < end:  # wait for more bytes
                return {}, -1
            else:
                request['body'] = s[start:end]
                end_of_req = end
        else:
            end_of_req = separation_idx + 2

        return request, end_of_req

    @staticmethod
    def get_path_root(request) -> str:
        return request["path"][1:].split('/')[0]

    def handle_request(self, request) -> bytes:
        if request["method"] == "GET":
            return self.handle_get(request)
        elif request["method"] == "POST":
            return self.handle_post(request)
        elif request["method"] == "DELETE":
            return self.handle_delete(request)
        else:
            return b'400  '

    def handle_get(self, request) -> bytes:
        path_root: str = self.get_path_root(request)
        if path_root == 'key':
            return self.store.get(request["path"])
        elif path_root == 'counter':
            return self.counter.get(request["path"])
        else:
            return b'400  '

    def handle_post(self, request) -> bytes:
        path_root: str = self.get_path_root(request)
        if path_root == 'key':
            return self.store.post(request["path"], request["body"])
        elif path_root == 'counter':
            return self.counter.post(request["path"])
        else:
            return b'400  '

    def handle_delete(self, request) -> bytes:
        path_root: str = self.get_path_root(request)
        if path_root == 'key':
            return self.store.delete(request["path"])
        else:
            return b'400  '


if __name__ == "__main__":
    port = int(sys.argv[1])
    server = WebServer(port_=port)
    server.start()
