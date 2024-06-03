import json
import socket
import time
from multiprocessing import Process
import os
import sys
import struct

dictionary = {}

def get(params):
    name = params["obj"]
    entry = dictionary.get(name)
    retval = {"obj": name, "val": entry}
    return retval

def put(params):
    name = params["obj"]
    val = params["val"]
    dictionary[name] = val
    retval = {"obj": name, "response": "ok"}
    return retval

def make_call(msg):
    func = msg["func"]
    param = msg["params"]
    if func == "GET":
        return {"func": "GET", "response": get(param)}
    elif func == "PUT":
        return {"func": "PUT", "response": put(param)}
    else:
        return {"func": func, "response": "ERROR - Function doesn't exist"}

def recv_message(conn):
    header = conn.recv(8)
    if len(header) < 8:
        raise ValueError("Incomplete header received")
    
    version, data_len = struct.unpack("ii", header)
    
    data = conn.recv(data_len)
    if len(data) < data_len:
        raise ValueError("Incomplete message received")
    
    json_string = data.decode()
    json_dict = json.loads(json_string)
    
    return json_dict

def send_message(conn, json_dict):
    json_blob = json.dumps(json_dict)
    len_blob = len(json_blob)
    hdr = struct.pack("ii", 1, len_blob)
    conn.send(hdr)
    conn.send(json_blob.encode())

def server_program():
    host = socket.gethostname()
    port = 4444

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))

    server_socket.listen(5)
    print("Server is listening...")

    while True:
        conn, address = server_socket.accept()
        print(f"Connection from {address} has been established.")

        try:
            json_dict = recv_message(conn)
            retval = make_call(json_dict)

            response = {"status": "OK", "response": retval}
            send_message(conn, response)
        except Exception as e:
            print(f"Error: {e}")
            error_response = {"status": "ERROR"}
            send_message(conn, error_response)
        finally:
            conn.close()

def client_do_single_call(call):
    host = socket.gethostname()
    port = 4444

    client_socket = socket.socket()
    client_socket.connect((host, port))

    send_message(client_socket, call)

    json_dict = recv_message(client_socket)

    client_socket.close()
    return json_dict

def client_do_single_call_wrapper(mode, call):
    if mode == "LOCAL":
        retval = make_call(call)
        return {"status": "OK", "response": retval}
    else:
        return client_do_single_call(call)

def test_client_program(mode):
    call1 = {"func": "GET", "params": {"obj": "ABC"}}
    ret1 = client_do_single_call_wrapper(mode, call1)
    print("Call:" + str(call1))
    print("Ret:" + str(ret1))
    
    call2 = {"func": "PUT", "params": {"obj": "HELLO", "val": "WORLD"}}
    ret2 = client_do_single_call_wrapper(mode, call2)
    print("Call:" + str(call2))
    print("Ret:" + str(ret2))

    call3 = {"func": "PUT", "params": {"obj": "ABC", "val": {"val1": 111, "val2": 222}}}
    ret3 = client_do_single_call_wrapper(mode, call3)
    print("Call:" + str(call3))
    print("Ret:" + str(ret3))

    call4 = {"func": "PUT", "params": {"obj": "DEF", "val": {"val1": 333, "val2": 444}}}
    ret4 = client_do_single_call_wrapper(mode, call4)
    print("Call:" + str(call4))
    print("Ret:" + str(ret4))

    call5 = {"func": "GET", "params": {"obj": "ABC"}}
    ret5 = client_do_single_call_wrapper(mode, call5)
    print("Call:" + str(call5))
    print("Ret:" + str(ret5))

    call6 = {"func": "GET", "params": {"obj": "DEF"}}
    ret6 = client_do_single_call_wrapper(mode, call6)
    print("Call:" + str(call6))
    print("Ret:" + str(ret6))

def main(argv):
    if len(argv) != 2:
        print("srpc <mode>")
        print("mode is one of LOCAL, CLIENT, SERVER, BOTH")
        return -1
    mode = argv[1]
    print(mode)
    if mode == "LOCAL" or mode == "CLIENT":
        test_client_program(mode)
    elif mode == "SERVER":
        server_program()
    elif mode == "BOTH":
        pServer = Process(target=server_program, args=())
        pServer.start()
        time.sleep(1)
        pClient = Process(target=test_client_program, args=('CLIENT',))
        pClient.start()
        pClient.join()
        pServer.terminate()
        pServer.join()
    else:
        print("srpc <mode>")
        print("mode is one of LOCAL, CLIENT, SERVER, BOTH")
        return -1
    return 0

if __name__ == "__main__":
    retval = main(sys.argv)
