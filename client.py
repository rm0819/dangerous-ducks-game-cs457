#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import struct
import logging

import clientMessage

sel = selectors.DefaultSelector()

# Set up logging for client
logger = logging.getLogger(__name__)
logging.basicConfig(filename="client.log", encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

def create_request(action, value):
    if action == "join_game":
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, value=value),
        )
    elif action == "message":
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, value=value),
        )
    else:
        return dict(
            type="binary/custom-client-binary-type",
            encoding="binary",
            content=bytes(action + value, encoding="utf-8"),
        )

def start_game_connection(host, port, request):
    addr = (host, int(port))
    print("starting connection to", addr)
    # Log connection to server
    logger.info("Connecting to server at %s on port %s", host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = clientMessage.Message(sel, sock, addr, request)
    sel.register(sock, events, data=message)
    
# -------------------- START TO GAME ------------------------
print("\nWelcome to Battleship!")
host, port = input("Please enter the host and port you'd like to connect to: ").split()
if (not host or not port):
    print("Enter host and port as such: <host> <port>")
    sys.exit(1)

# Get board configuration
board = input("\nPlease enter your ship positions:\n")

#action, value = sys.argv[3], sys.argv[4]
request = create_request("join_game", board)
start_game_connection(host, port, request)

print("Connected to the server!")


try:
    while True:
        events = sel.select(timeout=1)
        for key, mask in events:
            message = key.data
            try:
                message.process_events(mask)
            except Exception:
                print(
                    "main: error: exception for",
                    f"{message.addr}:\n{traceback.format_exc()}",
                )
                logger.info(
                    "main: error: exception for",
                    f"{message.addr}:\n{traceback.format_exc()}"
                )
                message.close()
        # If there are still sockets open then continue the program
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()