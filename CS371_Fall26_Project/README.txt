CONTACT INFO
============

Group Members & Email Addresses:

    Jacob Kulig,   jdku225@uky.edu
    Noella Kule,   nku239@uky.edu
    Shaddai Ngoyi, sng234@uky.edu

VERSIONING
==========

Github Link: https://github.com/shadd-33/371-Project-

Git and GitHub are used for version control and collaborative development. 
Each group member contributes to the project through commits and updates to the shared repository.

GENERAL INFO
============
This project is a multiplayer implementation of the classic Pong game using Python and a
client-server architecture.
 
The server runs the game: it tracks both paddles, the ball, and the score, and sends the
official game state to both clients about 60 times per second. The clients provide the graphical game interface 
and allow players to control their paddles.

Socket programming and multithreading are used to support communication between the server and both clients.

Files:
    pong/pongServer.py   The server that hosts the game
    pong/pongClient.py   The client (start screen + game window)
    pong/assets/         Fonts, images, sounds and helper code provided with the project
    requirements.txt     Python libraries needed to run the project
    README.txt           This current file

You can find more information about running this program below in the 'Running the Program' Section.

REQUIREMENTS
============
Python 3
Pygame 2.5.2
Any Additional dependencies listed in requirements.txt

INSTALL INSTRUCTIONS
====================
First clone the project repository then navigate to the project directory.

Run the following line to install the required libraries for this project:

`pip3 install -r requirements.txt`

If uisng a Mac, make sure to download the latest python version. Most Mac use Apple’s built-in Tk 8.5. 
Tk 8.5 can’t read PNG files, so you'll run into image rendering issues. while Tk 8.6 or higher can read PNG files correctly. 

Recommeded command: 'python3.12 -m pip install -r requirements.txt'

RUNNING THE PROGRAM
====================

Starting the Server

[Instructions to be added after server implementation.]

Connecting the Clients

[Instructions to be added after client implementation.]

Known Bugs
==========
- The server doesn't work because the logic isn't yet written.
- The client doesn't speak to the server

