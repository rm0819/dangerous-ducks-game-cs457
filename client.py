#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import struct
import logging

class Client:
    def __init__(self, sel, sock, serverAddr, request):
        self.selector = sel
        self.sock = sock
        self.serverAddr = serverAddr
        self.recv_buffer = b""
        self.send_buffer = []
        self.request = request
        self.response_created = False

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
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                f"error: selector.unregister() exception for",
                f"{self.serverAddr}: {repr(e)}",
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                f"error: socket.close() exception for",
                f"{self.serverAddr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def message_decode(self, data):
        readable = data.decode("utf-8")
        if readable[0] == "0": # Info message from the server
            print(readable[2:])
        elif readable[0] == "1": # Request for information from the server
            print(readable[2:])
            # Read the data, its time to write
            self.set_selector_events_mask("w")
        elif readable[0] == "2": # Message containing ship board
            print("Updated ship board:")
            print(readable[2:])
        elif readable[0] == "3": # Message containing attack board
            print("Updated attack board:")
            print(readable[2:])
        else:
            print("There was an error receiving data from the server.")
    
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
                raise RuntimeError("Peer closed.")
            
    # Sends whatever data is in the request variable to the server
    def write(self):
        for req in self.send_buffer: # if there is something to send
            # Get the player that the request is being sent to
            print("sending", repr(req), "to", self.serverAddr)
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
    
    def get_request_data(self):
        if self.request == None:
            playerInput = input("What move would you like to input? ")
            while len(playerInput) != 2:
                print("=== Error: Input must be in the form of <#><letter>. Ex. 2D ===")
                playerInput = input("What move would you like to input? ")
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
logging.basicConfig(filename="client.log", encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

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
            client = key.data
            try:
                # Checks if the client is reading or writing, and if the server sent us any data
                client.process(mask)
            except Exception:
                print(
                    "main: error: exception for",
                    f"{client}:\n{traceback.format_exc()}",
                )
                logger.info(
                    "main: error: exception for",
                    f"{client}:\n{traceback.format_exc()}"
                )
                client.close()
        # If there are still sockets open then continue the program
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()