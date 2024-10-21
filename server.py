#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import logging
import random

sel = selectors.DefaultSelector()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename="server.log", encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

letters_to_numbers = {
    'A': '0',
    'B': '1',
    'C': '2',
    'D': '3',
    'E': '4',
    'F': '5',
    'G': '6',
    'H': '7',
    'I': '8',
    'J': '9'
}
send_buffer = b""
empty_board = "........../........../........../........../........../........../........../........../........../........../"
players = []

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    # Log connection
    logger.info("Accepted connection from %s on port %s", addr[0], addr[1])
    conn.setblocking(False)
    # message = serverMessage.Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=conn)

def join_game(data, socket):
    players.append([data, empty_board, socket])
    if len(players) == 1:
        send_buffer += "0" + "Waiting for Player 2"
    else:
        send_buffer += "0" + "Game Starting..."
    
def pass_turn(data, socket):
    if(players[0][2] == socket):
        current_player = 0
        target = 1
    else:
        current_player = 1
        target = 0
    vertical = data[0]
    horizontal = letters_to_numbers[data[1]]
    index = (vertical * 11) + horizontal
    index_value = players[target][0][index]
    if(index_value != "." or index_value != "O"):
        #hit
        players[target][0][index] = "X"
        players[current_player][1][index] = "X"
    else:
        #miss
        players[target][0][index] = "O"
        players[current_player][1][index] = "O"
        pass
    send_buffer += "1" +  players[current_player][0] + players[current_player][1]

def message_decode(data, socket):
    readable = data.decode()
    if readable[0] == 0:
        join_game(readable[1:], socket)
    elif readable[0] == 1:
        pass_turn(readable[1:], socket)
    else:
        pass
        # error!

def read(conn):
    try:
        # Should be ready to read
        data = conn.recv(111)
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
                    if mask & selectors.EVENT_READ:
                        read(message)
                    if mask & selectors.EVENT_WRITE:
                        write(message)
                except Exception:
                    print(
                        "main: error: exception for",
                        f"{message}:\n{traceback.format_exc()}",
                    )
                    logger.info(
                        "main: error: exception for",
                        f"{message}:\n{traceback.format_exc()}"
                    )
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()



