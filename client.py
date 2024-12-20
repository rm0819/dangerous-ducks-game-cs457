#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import struct
import logging
import argparse

class Client:
    def __init__(self, sel, sock, serverAddr, request):
        self.selector = sel
        self.sock = sock
        self.serverAddr = serverAddr
        self.recv_buffer = []
        self.send_buffer = []
        self.request = request
        self.response_created = False
        self.numbers_to_letters = {
            0: 'A',
            1: 'B',
            2: 'C',
            3: 'D',
            4: 'E',
            5: 'F',
            6: 'G',
            7: 'H',
            8: 'I',
            9: 'J'
        }

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
        self.selector.modify(self.sock, events, data=self)

    def close(self):
        print("closing connection to", self.serverAddr)
        logger.info("Closed connection to %s", self.serverAddr)
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                f"error: selector.unregister() exception for",
                f"{self.serverAddr}: {repr(e)}",
            )
            logger.error(
                f"error: selector.unregister() exception for %s: %s",
                self.serverAddr, repr(e)
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                f"error: socket.close() exception for",
                f"{self.serverAddr}: {repr(e)}",
            )
            logger.error(
                "error: socket.close() exception for %s: %s",
                self.serverAddr, repr(e)
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def message_decode(self, data):
        decodedData = data.decode("utf-8")
        for i in range(decodedData.count("~")):
            info = decodedData[2:decodedData.index("~")]
            logger.info("Received %s from %s", info, self.serverAddr)
            if decodedData[0] == "0": # Info message from the server
                print(info)
            elif decodedData[0] == "1": # Request for information from the server
                print(info)
                # Read the data, its time to write
                self.set_selector_events_mask("w")
            elif decodedData[0] == "2": # Message containing ship board
                print("Your ships and enemy attacks:")
                self.print_formatted_board(info)
            elif decodedData[0] == "3": # Message containing attack board
                print("Your attacks:")
                self.print_formatted_board(info)
            elif decodedData[0] == "4":
                print(info)
                inp = input("Would you like to play again? y/n: ")
                if inp.lower() == "y":
                    sel.unregister(self.sock)
                    req = b"0" + board.encode("utf-8") 
                    start_game_connection(host, port, req)
                    print("Connecting to the server to play again!")
                    logger.info("Connecting to the server to play again.")
                else:
                    print("Exiting program...")
                    logger.info("Exiting program.")
                    sys.exit()
            elif decodedData[0] == "5": # Message saying the server stopped, and the reason why
                print(info)
                print("Exiting program...")
                logger.info("Exiting program.")
                sys.exit()
            else:
                print("There was an error receiving data from the server.")
                logger.info("Unexpected error getting info from the server from: %s", self.serverAddr)
            
            decodedData = decodedData[decodedData.index("~") + 1:]

    def print_formatted_board(self, board):
        formatted_board = board.replace("/", "\n")
        # Column labels
        print("   ", end="")
        for i in range(10):
            print(self.numbers_to_letters[i] + " ", end="")
        print()

        row = 0
        for i in formatted_board:
            # Row labels
            if row % 11 == 0:
                if row // 11 == 9: # if the last row
                    print(str((row // 11) + 1) + " ", end="")
                else: # all other rows
                    print(str((row // 11) + 1) + "  ", end="")
            row += 1

            if i == "\n":
                print(i, end="")
            else:
                print(i + " ", end="")
        print()
    
    def read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError as error:
            pass
        else:
            if data:
                # process data
                self.message_decode(data)
            else:
                raise RuntimeError("Peer closed.") # Change to handle server closing and client disconnecting
            
    # Sends whatever data is in the request variable to the server
    def write(self):
        for req in self.send_buffer: # if there is something to send
            # Get the player that the request is being sent to
            print("sending", repr(req), "to", self.serverAddr)
            logger.info("sending %s to %s", repr(req), self.serverAddr)
            try:
                # Send the data to the specified player
                self.sock.send(req)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                pass

        # Clear request and buffer after all information has been sent
        self.send_buffer.clear()
        self.request = None

        if len(self.send_buffer) == 0:
            self.set_selector_events_mask("r") # We sent all our data, listen for a response now
    
    def input_sanitizing(self, input):
        if len(input) != 2 and len(input) != 3:
            print("Your coordinate was invalid. Pick a valid coordinate on the board, in <letter><number> format. Try again.")
            return None
        if len(input) == 2:
            if ord(input[1]) < 49 or ord(input[1]) > 57:
                print("Your number was invalid. Pick a valid number on the board, from 1 to 10. Try again.")
                return None
        if len(input) == 3:
            if ord(input[1]) != 49 or ord(input[2]) != 48:
                print("Your number was invalid. Pick a valid number on the board, from 1 to 10. Try again.")
                return None
        vertical = int(input[1:]) - 1
        horizontal = ord(input[0]) - 65
        if vertical < 0 or vertical > 9:
            print("Your number was invalid. Pick a valid number on the board, from 1 to 10. Try again.")
            if horizontal < 0 or horizontal > 9:
                print("Your letter was invalid. Pick a valid number on the board, from A to J. Try again.")
            return None
        if horizontal < 0 or horizontal > 9:
            print("Your letter was invalid. Pick a valid number on the board, from A to J. Try again.")
            return None
        return input

    def get_request_data(self):
        if self.request == None:
            retry_prompt = True
            while(retry_prompt):
                playerInput = input("What tile would you like to attack? ")
                safe_input = self.input_sanitizing(playerInput)
                if safe_input is not None:
                    retry_prompt = False
                    self.request = ("1" + str(playerInput)).encode("utf-8")
                    self.send_buffer.append(self.request)
        else:
            self.send_buffer.append(self.request)

    def process(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.get_request_data()
            self.write()


# =================================================
# ========== START OF THE CLIENT PROGRAM ==========
sel = selectors.DefaultSelector()

# Set up logging for client
logger = logging.getLogger(__name__)
logging.basicConfig(filename="client.log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# non-class usage for initialize. can probably use for class as well but I dont want to break anything rn
def print_formatted_board(board):
        
        numbers_to_letters = {
            0: 'A',
            1: 'B',
            2: 'C',
            3: 'D',
            4: 'E',
            5: 'F',
            6: 'G',
            7: 'H',
            8: 'I',
            9: 'J'
        }

        formatted_board = board.replace("/", "\n")
        # Column labels
        print("   ", end="")
        for i in range(10):
            print(numbers_to_letters[i] + " ", end="")
        print()

        row = 0
        for i in formatted_board:
            # Row labels
            if row % 11 == 0:
                if row // 11 == 9: # if the last row
                    print(str((row // 11) + 1) + " ", end="")
                else: # all other rows
                    print(str((row // 11) + 1) + "  ", end="")
            row += 1

            if i == "\n":
                print(i, end="")
            else:
                print(i + " ", end="")
        print()

def placement_validator(board, coordinate, direction, size, boat_number):
    board = list(board)
    if len(coordinate) != 2 and len(coordinate) != 3:
        print("Your coordinate was invalid. Pick a valid coordinate on the board, in <letter><number> format. Try again.")
        return None
    if len(coordinate) == 2:
        if ord(coordinate[1]) < 49 or ord(coordinate[1]) > 57:
            print("Your number was invalid. Pick a valid number on the board, from 1 to 10. Try again.")
            return None
    if len(coordinate) == 3:
        if ord(coordinate[1]) != 49 or ord(coordinate[2]) != 48:
            print("Your number was invalid. Pick a valid number on the board, from 1 to 10. Try again.")
            return None
    vertical = int(coordinate[1:]) - 1
    horizontal = ord(coordinate[0]) - 65
    if vertical < 0 or vertical > 9:
        print("Your number was invalid. Pick a valid number on the board, from 1 to 10. Try again.")
        if horizontal < 0 or horizontal > 9:
            print("Your letter was invalid. Pick a valid number on the board, from A to J. Try again.")
        return None
    if horizontal < 0 or horizontal > 9:
            print("Your letter was invalid. Pick a valid number on the board, from A to J. Try again.")
            return None
    index = (vertical * 11) + horizontal
    if direction == "up": 
        step_by = -11
    elif direction == "down":
        step_by = 11
    elif direction == "left":
        step_by = -1
    elif direction == "right":
        step_by = 1
    else:
        print("Your direction was invalid. Your options are (up, down, left, right). Try again.")
        return None
            
    for i in range(size):
                if index >= 0 and index < len(board):
                    if board[index] == '.':
                        board[index] = str(boat_number)
                        index += step_by
                    elif board[index] == '/':
                        print("Your entry left the boundaries of the board! Try again.")
                        return None
                    else:
                        print("Your entry intersected with an existing ship! Try again.")
                        return None
                else:
                    print("Your entry left the boundaries of the board! Try again.")
                    return None
    return ''.join(board)
                
def initialize_board():
    ship_types = ("Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer")
    ship_lengths = (5,4,4,3,2)
    board = "........../........../........../........../........../........../........../........../........../.........."
    print("First, lets place your ships. You have a Carrier (Length 5), Battleship (Length 4), Cruiser (Length 3), Submarine (Length 3), and Destroyer (Length 2)")
    print("Your empty board looks like this: ")
    print_formatted_board("".join(board))
    print("For each ship, pick a starting coordinate and direction (up, down, left, right)")
    print("ie: C2 down")
    for i in range(5):
        retry_prompt = True
        while(retry_prompt):
            user_input = input(f"Input a starting coordinate and direction for your {ship_types[i]} (Length {ship_lengths[i]}).\n")
            if user_input.count(" ") == 1:
                coordinate, direction = user_input.split()
                validate_value = placement_validator(board, coordinate.upper().strip(), direction.lower().strip(), ship_lengths[i], i+1)
            else:
                print("Your input is invalid. For each ship, pick a starting coordinate and direction (up, down, left, right)")
                print("ie: C2 down")
                validate_value = None
            if validate_value is not None:
                board = validate_value
                retry_prompt = False
                print("Your board now looks like this:")
                print_formatted_board(board)
    return board

def start_game_connection(host, port, request):
    addr = (host, int(port))
    print("starting connection to", addr)
    # Log connection to server
    logger.info("Connecting to server at %s on port %s", host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_WRITE
    # Creates a client object, which handles sending data to the server and receiving data as well
    client = Client(sel, sock, addr, request)
    sel.register(sock, events, data=client)
    
# -------------------- START TO GAME ------------------------
print("\nWelcome to Battleship!")
logger.info("Starting program.")

parser = argparse.ArgumentParser(description='Server for Battleship terminal game')
parser.add_argument('-i', help='Server IP', required=True)
parser.add_argument('-p', help='Server port', required=True)
args = parser.parse_args()

host, port = (args.i, args.p)

if (not host or not port):
    print("Enter host and port as such: <host> <port>")
    sys.exit(1)

# Hardcode:
#board = "11111...../2222....../3333....../444......./55......../........../........../........../........../.........."
#board =  "1........./........../........../........../........../........../........../........../........../.........."
# cli input:
# board = input("\nPlease enter your ship positions:\n")

# Real:
board = initialize_board()
logger.info("Initialized player board information.")

#action, value = sys.argv[3], sys.argv[4]
request = b"0" + board.encode("utf-8") 
start_game_connection(host, port, request)

print("Connected to the server!")
logger.info("Connected to the server at %s on port %s", host, port)

try:
    while True:
        events = sel.select(timeout=1)
        for key, mask in events:
            client = key.data
            try:
                # Checks if the client is reading or writing, and if the server sent us any data
                client.process(mask)
            except Exception:
                print(
                    "main: error: exception for",
                    f"{client}:\n{traceback.format_exc()}",
                )
                logger.error(
                    "main: error: exception for %s: %s",
                    client, traceback.format_exc()
                )
                client.close()
        # If there are still sockets open then continue the program
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
    logger.info("Caught keyboard interrupt, exiting program")
finally:
    sel.close()