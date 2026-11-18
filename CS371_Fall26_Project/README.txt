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
client-server architecture to allow two players to connect and play against each other.
 
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

You can find more information about how to run this program below in the 'Running the Program' Section.

REQUIREMENTS
============

Python 3.12 (hightly recommended)
Pygame 2.5.2 (listed in requirements.txt)
Additional dependencies listed in requirements.txt

INSTALL INSTRUCTIONS
====================
First clone the project repository then navigate to the project directory.
Run the following line to install the required libraries for this project:

`pip3 install -r requirements.txt`

Windows / Linux:
    Python 3.12 works as is. Use `python` or `python3` in the commands below.
 
macOS:
    Apple's built-in Python uses Tk 8.5, which cannot read PNG files, so Tkinter will not display 
    the provided PNG logo causing the client to crash on the start screen with an error message: "couldn't recognize data in image file".
    Install Python 3.12 from python.org (the macOS installer includes Tk 8.6 or higher), then run:
 
        python3.12 -m pip install -r requirements.txt
 
    Do not use the newest Python release (e.g. 3.15 or 3.16): pygame 2.5.2 has no prebuilt package
    for it, so the install tries to compile pygame and fails.

RUNNING THE PROGRAM
====================

** Starting the Server **

1. Open a terminal.
2. Navigate to the pong directory: (cd pong)
3. To start the server: 
Windows : python3 pongServer.py 
macOS : python3.12 pongServer.py

Keep the server terminal open while players connect.
The server listens for incoming player connections on port 5555.

** Connecting the Clients **

1. Open a separate terminal for each player.
2. Navigate to the pong directory. (cd pong)
3. Start the client:
Windows: python3 pongClient.py
macOS : python3.12 pongClient.py

- Enter the server IP address and port number in the connection window.
For players connecting from the same computer, use 127.0.0.1 as the server IP address.
For players connecting from different computers, use the IP address of the computer hosting the server.

- Server Port: 5555
Both players must connect before the multiplayer game can begin.

** Network Notes **
 
    - Clients on different computers must be able to reach the server's IP address and port.
      If you are off campus, connect to the UK VPN first:
      https://www.cs.uky.edu/docs/users/vpn.html
    - If a client cannot connect, make sure the server's firewall allows Python on port 5555.
    - The server must be restarted to play another game.


GAME CONTROLS
==========

- Up Arrow: Move paddle upward.
- Down Arrow: Move paddle downward.


KNOWN BUGS
==========

- Only two players are supported. If either player disconnects, the server shuts down.
* There is no "Play Again" feature at the current moment. After a player reaches 5 points, the server must be
  restarted for a new game.
- A paddle moves 5 pixels for every input message the server receives, so paddle speed
  depends on how fast the client sends messages (60 per second at full frame rate).
- The "sync" counter is sent and stored, but it is not used to resynchronize the clients.
  The server is authoritative, so every state message corrects the clients.
* There is no player authentication or encryption for now as well. Messages are sent in plain text. 


