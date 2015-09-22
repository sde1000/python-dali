#!/usr/bin/env python

import socket

__author__ = 'psari'

TCP_IP = '127.0.0.1'
TCP_PORT = 55825
BUFFER_SIZE = 20  # Normally 1024, but we want fast response

while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    conn, addr = s.accept()

    try:
        print("Connection address:", addr)
        while 1:
            conn.setblocking(0)
            conn.settimeout(20.0)
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break

            stream = ":".join("{:02x}".format(ord(chr(c))) for c in data)
            print("received data: [{1}] {0}".format(stream, len(data)))

            # conn.send(data)  # echo
            conn.send(b"\x02\xff\x00\x00")
    except:
        pass

    conn.close()
