#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import struct
import logging

sel = selectors.DefaultSelector()

# Set up logging for client
logger = logging.getLogger(__name__)
logging.basicConfig(filename="client.log", encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

send_buffer = b""

def message_decode(data, socket):
    readable = data.decode()
    if readable[0] == 0:
        print(readable[1:])
    elif readable[0] == 1:
        print(readable[1:])
    else:
        pass
        # error!

def read(conn):
    try:
        # Should be ready to read
        data = conn.recv(4096)
    except BlockingIOError as error:
        pass
    else:
        if data:
            # process data
            message_decode(data, conn)
        else:
            raise RuntimeError("Peer closed.")

def write(conn):
    if send_buffer:
        print("sending", repr(send_buffer), "to", conn.addr)
        try:
            # Should be ready to write
            sent = conn.sock.send(send_buffer)
        except BlockingIOError as error:
            pass
        else:
            send_buffer = send_buffer[sent:]
            # Close when the buffer is drained. The response has been sent.
            #if sent and not self._send_buffer:
                #self.close()

def start_game_connection(host, port, request):
    addr = (host, int(port))
    print("starting connection to", addr)
    # Log connection to server
    logger.info("Connecting to server at %s on port %s", host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    # message = clientMessage.Message(sel, sock, addr, request)
    send_buffer = request
    sel.register(sock, events, data=sock)
    
# -------------------- START TO GAME ------------------------
print("\nWelcome to Battleship!")
host, port = input("Please enter the host and port you'd like to connect to: ").split()
if (not host or not port):
    print("Enter host and port as such: <host> <port>")
    sys.exit(1)

# Get board configuration
board = input("\nPlease enter your ship positions:\n")

#action, value = sys.argv[3], sys.argv[4]
request = b"0" + board.encode("utf-8") 
start_game_connection(host, port, request)

print("Connected to the server!")

try:
    while True:
        events = sel.select(timeout=1)
        for key, mask in events:
            message = key.data
            try:
                if mask & selectors.EVENT_READ:
                    read(message)
                if mask & selectors.EVENT_WRITE:
                    message.send(request)
            except Exception:
                print(
                    "main: error: exception for",
                    f"{message}:\n{traceback.format_exc()}",
                )
                logger.info(
                    "main: error: exception for",
                    f"{message}:\n{traceback.format_exc()}"
                )
                message.close()
        # If there are still sockets open then continue the program
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()