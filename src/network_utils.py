import json
import socket

def sendall(sock: socket.socket, obj: str | dict):
    if type(obj) == str:
        sock.sendall(obj.encode("utf-8"))
    elif type(obj) == dict:
        sock.sendall(json.dumps(obj).encode("utf-8"))
    else:
        raise TypeError("Expected object types are str or dict, get {}".format(type(obj)))
    
def recvall(sock: socket.socket, bufsize: int) -> str:
    fragments = []
    while True:
        try:
            sock.settimeout(0.5)
            chunk = sock.recv(bufsize)
        except socket.timeout:
            break
        fragments.append(chunk.decode("utf-8"))
    return ''.join(fragments)

