# Table of Contents
- [Introduction](#title)
- [Scope of Work](#sow)
- [Technical Details](#technical-details)

<br/>

# Dangerous Ducks' Battleship Game <a name="title"></a>

This is a simple network battleship game implemented using Python and sockets. 

**How to play:**
1. **Start the server:** Not set up yet!
2. **Connect clients:** Not set up yet!
3. **Play the game:** Players will take turns entering their moves. Player 1 will enter a move, then wait for player 2's response if its a hit. First player to hit every spot on all the enemy battleships wins!

**Technologies used:**
* Python
* Sockets

**Additional resources:**
* [Battleship Rules](https://www.hasbro.com/common/instruct/battleship.pdf)
* [Link to Python documentation](https://docs.python.org/3/)
* [Link to sockets tutorial](https://docs.python.org/3/howto/sockets.html)

<br/>

# SOW
## Project Title:
[Insert Project Title]

## Team:
[Insert members of team]

## Project Objective:
[Briefly describe the goal of the project. What problem are you trying to solve or what functionality are you aiming to achieve?]

## Scope:
### Inclusions:
[List the specific tasks, features, or components that will be included in the project.]
### Exclusions:
[List any tasks, features, or components that will not be included in the project.]
## Deliverables:
[List the expected outputs or deliverables from the project, such as a working Python script, documentation, or presentations.]
## Timeline:
### Key Milestones:
[Outline the major milestones or checkpoints throughout the project, with estimated completion dates.]
### Task Breakdown:
[Create a detailed breakdown of tasks, assigning estimated hours or days to each.]
## Technical Requirements:
### Hardware:
[Specify any hardware requirements, such as servers, networking equipment, or specific devices.]
### Software:
[List the necessary software tools, programming languages (Python), libraries (socket, threading, etc.), and operating systems.]
## Assumptions:
[State any assumptions that are being made about the project, such as network connectivity or availability of resources.]
## Roles and Responsibilities:
[Define the roles of team members, including project manager, developers, testers, etc., and their responsibilities.]
## Communication Plan:
[Outline the communication channels and frequency for project updates, meetings, and decision-making.]
## Additional Notes:
[Include any other relevant information or considerations that are specific to your project.]

<br/>

# Technical Details
The game can be implemented in multiple ways. Two possible ways are:
  1. Players both input their battleship positions, which are stored in some matrix. When one player sends their attack to the other, the server will verify if it is a "hit".
  2. Same input, but the players themselves send a response verifying it was a "hit" or "miss", like the original battleship game

<br/>

#### Grid Size
The grid will be 10x10.
Example board setup:
| |1 |2 |3 |4 |5 |6 |7 |8 |9 |10 |
| - | - | - | - | - | - | - | - | - | - | - |
|A | | | | | | | | | | |
|B | | | | | | | | | | |
|C | | | | | | | | | | |
|D | | | | | | | | | | |
|E | | | | | | | | | | |
|F | | | | | | | | | | |
|G | | | | | | | | | | |
|H | | | | | | | | | | |
|I | | | | | | | | | | |
|J | | | | | | | | | | |

#### Ship Sizes
| Ship              |   Size   |
| :---------------- | :------: |
| Carrier | 5 |
| Battleship | 4 | 
| Cruiser | 3 | 
| Submarine | 3 |
| Destroyer | 2 |
