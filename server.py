#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import logging
import random

class ServerData:
    # players holds 3 things in the list
    # Ship positions board holds your ships positions, and your enemies hits and misses
    # | ship positions board | board containing hits and misses | socket |
    players = []
    first = 0
    second = 1

class ClientConnection:
    def __init__(self, sel, sock, addr):
        self.sel = sel
        self.sock = sock
        self.addr = addr
        self.recv_buffer = b""
        self.send_buffer = []
        self.request = None
        self.response_created = False
        self.empty_board = "........../........../........../........../........../........../........../........../........../........../"
        self.letters_to_numbers = {
            'A': 0,
            'B': 1,
            'C': 2,
            'D': 3,
            'E': 4,
            'F': 5,
            'G': 6,
            'H': 7,
            'I': 8,
            'J': 9
        }

    def close(self):
        print("closing connection to", self.addr)
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                f"error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                f"error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.sel.modify(self.sock, events, data=self)
    
    def join_game(self, data):
        p.players.append([data, self.empty_board, self.sock])
        if len(p.players) == 1:
            self.request = ("00" + "Waiting for Player 2").encode("utf-8")
            self.send_buffer.append(self.request) 
        else:
            # Send a message to each player saying the game is starting
            self.request = ("00" + "All players are here. Game Starting...").encode("utf-8")
            self.send_buffer.append(self.request) 
            self.request = ("01" + "All players are here. Game Starting...").encode("utf-8")
            self.send_buffer.append(self.request) 

            # Determine which player is going first
            if random.randint(0,1) == 0: # if 0, player 2 goes first
                p.first = 1
                p.second = 0

            # Send an info request to starting player asking for info, and a message to the other playing saying waiting for player 1's move
            self.request = ("0" + str(p.second) + "Player " + str(p.first + 1) + " is going first. Waiting for their move...").encode("utf-8")
            self.send_buffer.append(self.request)
            self.request = ("1" + str(p.first) + "You are going first! Please enter which tile you would like to attack (Ex. 1A):").encode("utf-8")
            self.send_buffer.append(self.request)

    def pass_turn(self, data):
        if(p.players[0][2] == self.sock):
            current_player = 0
            target = 1
        else:
            current_player = 1
            target = 0
        vertical = int(data[0]) - 1
        horizontal = self.letters_to_numbers[data[1]]
        index = (vertical * 11) + horizontal
        index_value = p.players[target][0][index].lower()
        if index_value != "." and index_value != "o":
            #hit
            p.players[target][0][index] = "x"
            p.players[current_player][1][index] = "x"
        else:
            #miss
            updated_target_ship_board = p.players[target][0][:index] + "o" + p.players[target][0][index + 1:]
            updated_current_player_attack_board = p.players[current_player][1][:index] + "o" + p.players[current_player][1][index + 1:]
            p.players[target][0] = updated_target_ship_board
            p.players[current_player][1] = updated_current_player_attack_board

        # Send the player inputting the attack their updated attack board
        self.request = ("3" + str(current_player) + p.players[current_player][1]).encode("utf-8")
        self.send_buffer.append(self.request)
        # Send the other player their updated ship board
        self.request = ("2" + str(target) + p.players[target][0]).encode("utf-8")
        self.send_buffer.append(self.request)

        # CHECK GAME STATE (is the game over, has a ship been sunk, etc.)
        self.check_game_state()

        # Request attack move from the other player
        self.request = ("1" + str(target) + "Please enter which tile you would like to attack (Ex. 1A):").encode("utf-8")
        self.send_buffer.append(self.request)

    def check_game_state(self):
        # Needs to check boards to see if any ships are completely sunk, or if all ships have been sunk
        pass


    def message_decode(self, data):
        readable = data.decode("utf-8")
        if readable[0] == "0":
            self.join_game(readable[1:])
        elif readable[0] == "1":
            self.pass_turn(readable[1:])
        else:
            pass
            # error!

    def read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError as error:
            pass
        else:
            if data:
                # process data
                print("received ", repr(data), "from", self.sock.getpeername())
                self.message_decode(data)
            else:
                raise RuntimeError("Peer closed.")
            
        self.set_selector_events_mask("w") # We read the data, we're writing now

    # Sends data to specified client
    def write(self):
        for req in self.send_buffer: # if there is something to send
            # Get the player that the request is being sent to
            player = p.players[int(req.decode("utf-8")[1])]
            print("sending  ", repr(req), "to", player[2].getpeername())
            try:
                # Send the data to the specified player
                player[2].send(req)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                pass
        
        # Clear after all requests have been sent
        self.send_buffer.clear()

        if len(self.send_buffer) == 0:
            self.set_selector_events_mask("r") # We sent all our data, listen for a response now

    def get_request_data(self): # This is for later, in case we need it
        if self.request == None:
            pass

    def process(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.get_request_data()
            self.write()


# =================================================
# ========== START OF THE SERVER PROGRAM ==========
sel = selectors.DefaultSelector()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename="server.log", encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Data structure to hold player values
p = ServerData()

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    # Log connection
    logger.info("Accepted connection from %s on port %s", addr[0], addr[1])
    conn.setblocking(False)
    clientConnection = ClientConnection(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=clientConnection)

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
                clientConnection = key.data
                try:
                    clientConnection.process(mask)
                except Exception:
                    print(
                        "main: error: exception for",
                        f"{clientConnection}:\n{traceback.format_exc()}",
                    )
                    logger.info(
                        "main: error: exception for",
                        f"{clientConnection}:\n{traceback.format_exc()}"
                    )
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
