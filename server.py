#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import logging
import random
import argparse

class ServerData:
    # players holds 3 things in the list
    # Ship positions board holds your ships positions, and your enemies hits and misses
    # | ship positions board | board containing hits and misses | socket |
    players = []

    # "Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer" sunk flags in that order for each player.
    ship_sunk_flags = [[False, False, False, False, False],[False, False, False, False, False]]
    first = 0
    second = 1
    first_wants_to_play_again = False
    second_wants_to_play_again = False
    reset_game = False

    def reset_game_data(self):
        self.players = []
        self.ship_sunk_flags = [[False, False, False, False, False],[False, False, False, False, False]]
        self.first = 0
        self.second = 1
        self.first_wants_to_play_again = False
        self.second_wants_to_play_again = False
        self.reset_game = False

class ClientConnection:
    def __init__(self, sel, sock, addr):
        self.sel = sel
        self.sock = sock
        self.addr = addr
        self.recv_buffer = b""
        self.send_buffer = []
        self.request = None
        self.response_created = False
        self.empty_board = "........../........../........../........../........../........../........../........../........../.........."
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
            self.request = ("1" + str(p.first) + "You are going first! Please enter which tile you would like to attack (Ex. A1):").encode("utf-8")
            self.send_buffer.append(self.request)

    def pass_turn(self, data):
        if(p.players[0][2] == self.sock):
            current_player = 0
            target = 1
        else:
            current_player = 1
            target = 0
        vertical = int(data[1:]) - 1
        horizontal = self.letters_to_numbers[data[0].upper()]
        index = (vertical * 11) + horizontal
        index_value = p.players[target][0][index].lower()
        if index_value != "." and index_value != "o":
            #hit
            updated_target_ship_board = p.players[target][0][:index] + "x" + p.players[target][0][index + 1:]
            updated_current_player_attack_board = p.players[current_player][1][:index] + "x" + p.players[current_player][1][index + 1:]
            p.players[target][0] = updated_target_ship_board
            p.players[current_player][1] = updated_current_player_attack_board
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
        end_game = self.check_game_state(current_player, target)
        if end_game:
            self.end_game(current_player, target)

        # Request attack move from the other player
        self.request = ("1" + str(target) + "Please enter which tile you would like to attack (Ex. A1):").encode("utf-8")
        self.send_buffer.append(self.request)

    def check_game_state(self, current_player, target):
        # Needs to check boards to see if any ships are completely sunk, or if all ships have been sunk
        # "Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"
        if '1' not in p.players[target][0]:
            if not p.ship_sunk_flags[target][0]:
                #Carrier Sunk
                #Telling attacker
                self.request = ("0" + str(current_player) + "You sunk Player " + str(target + 1) + "'s Carrier!").encode("utf-8")
                self.send_buffer.append(self.request)
                #Telling target
                self.request = ("0" + str(target) + "Player " + str(current_player + 1) + " sunk your Carrier!").encode("utf-8")
                self.send_buffer.append(self.request)

                p.ship_sunk_flags[target][0] = True
        if '2' not in p.players[target][0]:
            if not p.ship_sunk_flags[target][1]:
                #Battleship Sunk
                #Telling attacker
                self.request = ("0" + str(current_player) + "You sunk Player " + str(target + 1) + "'s Battleship!").encode("utf-8")
                self.send_buffer.append(self.request)
                #Telling target
                self.request = ("0" + str(target) + "Player " + str(current_player + 1) + " sunk your Battleship!").encode("utf-8")
                self.send_buffer.append(self.request)

                p.ship_sunk_flags[target][1] = True
        if '3' not in p.players[target][0]:
            if not p.ship_sunk_flags[target][2]:
                #Cruiser Sunk
                #Telling attacker
                self.request = ("0" + str(current_player) + "You sunk Player " + str(target + 1) + "'s Cruiser!").encode("utf-8")
                self.send_buffer.append(self.request)
                #Telling target
                self.request = ("0" + str(target) + "Player " + str(current_player + 1) + " sunk your Cruiser!").encode("utf-8")
                self.send_buffer.append(self.request)

                p.ship_sunk_flags[target][2] = True
        if '4' not in p.players[target][0]:
            if not p.ship_sunk_flags[target][3]:
                #Submarine Sunk
                #Telling attacker
                self.request = ("0" + str(current_player) + "You sunk Player " + str(target + 1) + "'s Submarine!").encode("utf-8")
                self.send_buffer.append(self.request)
                #Telling target
                self.request = ("0" + str(target) + "Player " + str(current_player + 1) + " sunk your Submarine!").encode("utf-8")
                self.send_buffer.append(self.request)

                p.ship_sunk_flags[target][3] = True
        if '5' not in p.players[target][0]:
            if not p.ship_sunk_flags[target][4]:
                #Destroyer Sunk
                #Telling attacker
                self.request = ("0" + str(current_player) + "You sunk Player " + str(target + 1) + "'s Destroyer!").encode("utf-8")
                self.send_buffer.append(self.request)
                #Telling target
                self.request = ("0" + str(target) + "Player " + str(current_player + 1) + " sunk your Destroyer!").encode("utf-8")
                self.send_buffer.append(self.request)

                p.ship_sunk_flags[target][4] = True
        #all target's ships sunk?
        if False not in p.ship_sunk_flags[target]:
            return True
        else: 
            return False
        
    def end_game(self, current_player, target):
        # Telling player who sent the final attack
        self.request = ("4" + str(current_player) + "You Win!").encode("utf-8")
        self.send_buffer.append(self.request)
        #Telling target
        self.request = ("4" + str(target) + "You Lose!").encode("utf-8")
        self.send_buffer.append(self.request)

    def message_decode(self, data):
        readable = data.decode("utf-8")
        if readable[0] == "0":
            self.join_game(readable[1:])
        elif readable[0] == "1":
            self.pass_turn(readable[1:])
        elif readable[0] == "2":
            self.play_again(readable[1:])
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
                # Client disconnected # IMPORTANT -- Update so if one person is connected, they can disconnect without breaking things
                if p.players[0][2] == self.sock:
                    playerNumber = 1
                    disconnected = 0
                else:
                    playerNumber = 0
                    disconnected = 1
                self.request = ("5" + str(playerNumber + 1) + "Player " + str(disconnected + 1) + " disconnected from the game. Stopping the server.").encode("utf-8")
                self.send_buffer.append(self.request)
                # Log and print disconnect error
                logger.info("Player " + str(disconnected + 1) + " disconnected from the game. Stopping the server.")
                print("Player " + str(disconnected + 1) + " disconnected from the game. Stopping the server.")
            
        self.set_selector_events_mask("w") # We read the data, we're writing now

    # Sends data to specified client
    def write(self):
        stopServer = False
        for req in self.send_buffer: # if there is something to send
            # Add character that shows its the end of the message to each request
            decodedReq = req.decode("utf-8")
            decodedReq = decodedReq + "~"
            req = decodedReq.encode("utf-8")
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

            # See if the server sent a server reset message
            if decodedReq[0] == "4":
                p.reset_game = True

            # See if the server sent a server close message
            if decodedReq[0] == "5":
                stopServer = True
        
        # Clear after all requests have been sent
        self.send_buffer.clear()

        if len(self.send_buffer) == 0:
            self.set_selector_events_mask("r") # We sent all our data, listen for a response now
        
        # If the server sent a server close message to any player, then stop the server
        if stopServer:
            print("Client disconnected, closing application.")
            logger.info("Client disconnected, close application.")
            sys.exit()

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

parser = argparse.ArgumentParser(description='Server for Battleship terminal game')
parser.add_argument('-p', help='Listening port', required=True)
args = parser.parse_args()

host, port = '0.0.0.0', int(args.p)
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
        if p.reset_game:
            logger.info("Game ended, reset server.")
            print("Game ended, resetting server.")
            print("listening on", (host, port))
            sel.unregister(p.players[0][2])
            sel.unregister(p.players[1][2])
            p.reset_game_data()
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
