# Table of Contents
- [Introduction](#title)
- [Scope of Work](#sow)
- [Technical Details](#technical-details)
- [Game Message Protocol](#game-message-protocol)

<br/>

# Dangerous Ducks' Battleship Game <a name="title"></a>

This is a simple network battleship game implemented using Python and sockets. 

**How to play:**
1. **Start the server:** python server.py \<host\> \<port\>
2. **Connect client to server:** python client.py, then follow instructions
3. **Play the game:** Players will take turns entering their moves. Player 1 will enter a move, then wait for player 2's response if its a hit. First player to hit every spot on all the enemy battleships wins!

**Technologies used:**
* Python
* Sockets

**Additional resources:**
* [Battleship Rules](https://www.hasbro.com/common/instruct/battleship.pdf)
* [Link to Python documentation](https://docs.python.org/3/)
* [Link to sockets tutorial](https://docs.python.org/3/howto/sockets.html)
* [Requirements.txt explanation](https://dev.to/eskabore/pip-freeze-requirementstxt-a-beginners-guide-5e2m)

<br/>

# SOW
## Project Title:
Dangerous Ducks' Network Battleship Game

## Team:
### Dangerous Ducks
- Andrew Di Tirro
- Matthew Smith

## Project Objective:
The goal of this project is to create a network battleship game that can be played in a command line interface. We hope to create a simple, efficient, and fun game that any computer can run!

## Scope:
### Inclusions:
[List the specific tasks, features, or components that will be included in the project.]

Implement client-server architecture capable of at least two simultaneous clients.

**Client** must take the following arguments
- -h (help show the player how to connect, and play)
- -i ip address of the server (required argument)
- -p listening port of the server
- -n DNS name of the server

**Server** must take the following arguments
- -h (help show the user how to run the server)
- -i host-ip
- -p port

### Exclusions:
[List any tasks, features, or components that will not be included in the project.]
- Web UI
- Other?
  
## Deliverables:
[List the expected outputs or deliverables from the project, such as a working Python script, documentation, or presentations.]
- Working Python script
- Detailed documentation on how to setup server and client
- A short video demo?

## Timeline:
### Key Milestones:
[Outline the major milestones or checkpoints throughout the project, with estimated completion dates.]
- [x] Sprint 0: Form teams, Setup Tools, Submit SOW [Template] (Sept 08-Sept 22)
- [x] Sprint 1: Socket Programming, TCP Client Server (Sept 22-Oct 06) 
- [x] Sprint 2: Develop Game Message Protocol, Manage Client connections (Oct 06-Oct 20)
- [ ] Sprint 3: Multi-player functionality, Synchronize state across clients. (Oct 20-Nov 03)
- [ ] Sprint 4: Game play, Game State (Nov 03-Nov 17)
- [ ] Sprint 5: Implement Error Handling and Testing (Nov 17-Dec 6)
  
### Task Breakdown:
[Create a detailed breakdown of tasks, assigning estimated hours or days to each.]
- Program base battleship game and design CLI output. EST: 4 hours
- Program server socket connection handling. EST: 2 hours
- Program client connecitons to server. EST: 2.5 hours
- Program multiplayer functionality with synchronized state across clients. EST: 4 hours
- Add gameplay and game state to the server and clients. EST: 3.5 hours]
- Implement error handling. EST: 1.5 hours
- Test game for bugs. EST: 1.5 hours
- Finalize any details. EST: 1 hour

## Technical Requirements:
### Hardware:
[Specify any hardware requirements, such as servers, networking equipment, or specific devices.]

**Required**
- A computer with a connection to itself.
  
**Recommended**
- Two computers able to communicate with each other.

### Software:
[List the necessary software tools, programming languages (Python), libraries (socket, threading, etc.), and operating systems.]
- Python
- Python libraries, including: socket, threading, possibly a battleship library
  
## Assumptions:
[State any assumptions that are being made about the project, such as network connectivity or availability of resources.]
- Any clients are able to connect to the server, through the local network or the internet.
- Any client machines are able to run python.
  
## Roles and Responsibilities:
[Define the roles of team members, including project manager, developers, testers, etc., and their responsibilities.]

**Developers**
- Matt Smith
- Andrew Di Tirro

**Creative Design**
- Andrew Di Tirro

**Error Handling**
- Matt Smith

**Testers**
- Andrew Di Tirro
- Matt Smith

## Communication Plan:
[Outline the communication channels and frequency for project updates, meetings, and decision-making.]
- We will communicate weekly over Discord.

Team members will check in twice a week to discuss weekly goals and state of affairs. One of these check-ins will be a virtual call meeting, used for in-depth discussion and planning.
## Additional Notes:
[Include any other relevant information or considerations that are specific to your project.]
- Nothing to report here yet!

<br/>

# Technical Details
The game can be implemented in multiple ways. Two possible ways are:
  1. Players both input their battleship positions, which are stored in some matrix. When one player sends their attack to the other, the server will verify if it is a "hit".
  2. Same input, but the players themselves send a response verifying it was a "hit" or "miss", like the original battleship game

<br/>

#### Grid Size
The grid will be 10x10.
| |1|2|3|4|5|6|7|8|9|10|
|:-:|-|-|-|-|-|-|-|-|-|-|
|A| | | | | | | | | | |
|B| | | | | | | | | | |
|C| | | | | | | | | | |
|D| | | | | | | | | | |
|E| | | | | | | | | | |
|F| | | | | | | | | | |
|G| | | | | | | | | | |
|H| | | | | | | | | | |
|I| | | | | | | | | | |
|J| | | | | | | | | | |

#### Ship Sizes
| Ship       | Size |
| :-------   |  :-: |
| Carrier    |   5  |
| Battleship |   4  | 
| Cruiser    |   3  | 
| Submarine  |   3  |
| Destroyer  |   2  |

# Game Message Protocol
This protocol defines what messages are sent from the server to the client and vice versa, as well as what content the messages hold.

## Message Structure
* Join game - index 0: This will be a byte string with a leading 0, followed by a byte string of the starting ship positions for the player
* Attack - index 1: This will be a byte string with a leading 1, followed by a tile index, ex: "A4"

## Message Types
* Join game - index 0: This includes the player's starting ship position, and tells the server that the player is joining the game
* Attack - index 1: This is how a player attacks the enemies ship, by entering a tile to "shoot" at on the enemy players board

## Message Format
All messages will be byte encoded, rather than json encoded
