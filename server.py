#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import logging

import serverMessage

sel = selectors.DefaultSelector()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename="server.log", encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Player boards
players = {}

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    # Log connection
    logger.info("Accepted connection from %s on port %s", addr[0], addr[1])
    conn.setblocking(False)
    message = serverMessage.Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=message)


if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Avoid bind() exception: OSError: [Errno 48] Address already in use
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                message = key.data
                try:
                    message.process_events(mask)
                    if not players:
                        players[message.sock] = message.board
                        print(players)
                    elif len(players) == 1:
                        players[message.sock] = message.board
                        print(players)
                    else:
                        message.create_and_send_game_full_response()
                except Exception:
                    print(
                        "main: error: exception for",
                        f"{message.addr}:\n{traceback.format_exc()}",
                    )
                    logger.info("main: error: exception for",
                        f"{message.addr}:\n{traceback.format_exc()}"
                    )
                    message.close()
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()