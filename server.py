#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import logging
import random

import serverMessage

sel = selectors.DefaultSelector()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename="server.log", encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

empty_board = "........../........../........../........../........../........../........../........../........../........../"
# Player boards
players = {}
player_socks = []


# . . . . . x . . o . . 
# 

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
    while len(players) < 1:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                message = key.data
                try:
                    message.process_events(mask)
                    players[message] = [message.board, empty_board]
                    player_socks.append(message)
                except Exception:
                    print(
                        "main: error: exception for",
                        f"{message.addr}:\n{traceback.format_exc()}",
                    )
                    logger.info("main: error: exception for",
                        f"{message.addr}:\n{traceback.format_exc()}"
                    )
                    message.close()

    # Switch players if coin lands on heads to randomize player start order
    '''coin_flip = random.randint(0,1)
    # Player 2 goes first
    if coin_flip == 1:
        temp = player_socks[0]
        player_socks[0] = player_socks[1]
        player_socks[1] = temp'''
    turnState = 0
    noResponse = True

    # send message to both players saying "Player x starts first!"


    while True: # Gameplay loop
        if noResponse:
            player_socks[turnState].create_and_send_response("Please enter the tile you wish to attack.")
            while True:
                events = sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        accept_wrapper(key.fileobj)
                    else:
                        message = key.data
                        try:
                            if (mask & selectors.EVENT_READ):
                                message.process_events(mask)
                                noResponse = False
                        except Exception:
                            print(
                                "main: error: exception for",
                                f"{message.addr}:\n{traceback.format_exc()}",
                            )
                            logger.info("main: error: exception for",
                                f"{message.addr}:\n{traceback.format_exc()}"
                            )
                            message.close()
        elif not noResponse:
            if turnState == 0:
                turnState = 1
            else:
                turnState = 0
            noResponse = True
        

except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()