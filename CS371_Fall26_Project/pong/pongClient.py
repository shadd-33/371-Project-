# =================================================================================================
# Contributing Authors: Noella Kule, Jacob Kulig, Shaddai Ngoyi
# Email Addresses: nku239@uky.edu, jkulig29@uky.edu, sng234@uky.edu
# Date: 11/18/2026
# Purpose: Implements the Pong client, allowing players to connect to the server, send paddle
#          movements, and receive game updates for synchronized multiplayer gameplay.
# Misc: Uses TCP sockets and JSON for client-server communication.
# =================================================================================================

import pygame
import tkinter as tk
import sys
import socket
import json
import threading
from assets.code.helperCode import *


# Receive JSON updates from the server in a separate thread.
# This prevents the game window from freezing while waiting for data.
def receiveUpdates(client: socket.socket, gameState: dict,
                   stateLock: threading.Lock, connectionStatus: dict) -> None:
    try:
        with client.makefile("r", encoding="utf-8") as reader:
            for line in reader:
                message = json.loads(line)
                if not isinstance(message, dict):
                    continue

                # Store the newest server state for the game loop.
                with stateLock:
                    gameState.clear()
                    gameState.update(message)
    except (OSError, ValueError) as error:
        print(f"Error receiving server updates: {error}")
    finally:
        connectionStatus["connected"] = False


# This is the main game loop. For the most part, you will not need to modify this.
# The sections where you should add to the code are marked. Feel free to change
# any part of this project to suit your needs.
def playGame(screenWidth: int, screenHeight: int, playerPaddle: str,
             client: socket.socket) -> None:
    # Pygame inits
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.init()

    # Constants
    WHITE = (255, 255, 255)
    clock = pygame.time.Clock()
    scoreFont = pygame.font.Font("./assets/fonts/pong-score.ttf", 32)
    winFont = pygame.font.Font("./assets/fonts/visitor.ttf", 48)
    pointSound = pygame.mixer.Sound("./assets/sounds/point.wav")
    bounceSound = pygame.mixer.Sound("./assets/sounds/bounce.wav")

    # Display objects
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    winMessage = pygame.Rect(0, 0, 0, 0)
    topWall = pygame.Rect(-10, 0, screenWidth + 20, 10)
    bottomWall = pygame.Rect(-10, screenHeight - 10, screenWidth + 20, 10)
    centerLine = []
    for i in range(0, screenHeight, 10):
        centerLine.append(pygame.Rect((screenWidth / 2) - 5, i, 5, 5))

    # Paddle properties and init
    paddleHeight = 50
    paddleWidth = 10
    paddleStartPosY = (screenHeight / 2) - (paddleHeight / 2)
    leftPaddle = Paddle(pygame.Rect(10, paddleStartPosY, paddleWidth, paddleHeight))
    rightPaddle = Paddle(pygame.Rect(screenWidth - 20, paddleStartPosY, paddleWidth, paddleHeight))
    ball = Ball(pygame.Rect(screenWidth / 2, screenHeight / 2, 5, 5), -5, 0)

    if playerPaddle == "left":
        opponentPaddleObj = rightPaddle
        playerPaddleObj = leftPaddle
    elif playerPaddle == "right":
        opponentPaddleObj = leftPaddle
        playerPaddleObj = rightPaddle
    else:
        # Spectators can see both paddles but control neither.
        playerPaddleObj = None
        opponentPaddleObj = None

    lScore = 0
    rScore = 0
    sync = 0

    # =========================================================================================
    # Networking setup: store the latest game state received from the server.
    # The receiving thread runs separately from the Pygame loop.
    gameState = {}
    stateLock = threading.Lock()
    connectionStatus = {"connected": True}
    receiverThread = threading.Thread(
        target=receiveUpdates,
        args=(client, gameState, stateLock, connectionStatus),
        daemon=True
    )
    receiverThread.start()
    # =========================================================================================

    running = True
    while running:
        # Wiping the screen
        screen.fill((0, 0, 0))

        # Getting keypress events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if playerPaddleObj is not None:
                    if event.key == pygame.K_r and (lScore >= 5 or rScore >= 5):
                        try:
                            message = {"rematch": True}
                            client.sendall((json.dumps(message) + "\n").encode("utf-8"))
                            print("Rematch requested!")
                        except OSError as error:
                            print(f"Unable to request rematch: {error}")

                    elif event.key == pygame.K_DOWN:
                        playerPaddleObj.moving = "down"
                    elif event.key == pygame.K_UP:
                        playerPaddleObj.moving = "up"

            elif event.type == pygame.KEYUP:
                if playerPaddleObj is not None:
                    if event.key in (pygame.K_DOWN, pygame.K_UP):
                        playerPaddleObj.moving = ""

        if not running:
            break

        # =========================================================================================
        # Your code here to send an update to the server on your paddle's information,
        # where the ball is and the current score.
        # Feel free to change when the score is updated to suit your needs/requirements.
        # The server expects a direction rather than a paddle coordinate.
        # Only players send paddle movements to the server.
        # Spectators receive updates without controlling anything.
        if playerPaddleObj is not None:
            direction = playerPaddleObj.moving

            if direction not in ("up", "down"):
                direction = "stop"

            message = {"direction": direction}

            try:
                client.sendall((json.dumps(message) + "\n").encode("utf-8"))
            except OSError as error:
                print(f"Unable to send paddle movement: {error}")
                break

        # Copy the newest state received from the server.
        with stateLock:
            latestState = gameState.copy()

        # Update the game using the server's official positions and scores.
        if latestState:
            leftPaddle.rect.y = latestState.get("paddle1_y", leftPaddle.rect.y)
            rightPaddle.rect.y = latestState.get("paddle2_y", rightPaddle.rect.y)
            ball.rect.x = latestState.get("ball_x", ball.rect.x)
            ball.rect.y = latestState.get("ball_y", ball.rect.y)

            oldLScore = lScore
            oldRScore = rScore
            lScore = latestState.get("score1", lScore)
            rScore = latestState.get("score2", rScore)

            # Play the point sound when the score changes.
            if lScore != oldLScore or rScore != oldRScore:
                pointSound.play()

            sync = latestState.get("sync", sync)
        # =========================================================================================

        # Update the player paddle and opponent paddle's location on the screen.
        # The server now controls both paddle positions.
        # We do not move them locally because that would cause synchronization problems.

        # If the game is over, display the win message.
        if lScore > 4 or rScore > 4:
            winText = "Player 1 Wins!" if lScore > 4 else "Player 2 Wins!"

            textSurface = winFont.render(winText, False, WHITE)
            textRect = textSurface.get_rect()
            textRect.center = (screenWidth // 2, screenHeight // 2 - 30)
            winMessage = screen.blit(textSurface, textRect)

            # Show rematch instructions.
            if playerPaddle == "spectator":
                rematchText = "Waiting for players to rematch..."
            else:
                rematchText = "Press R to Play Again"

            rematchFont = pygame.font.Font(None, 28)
            rematchSurface = rematchFont.render(rematchText, True, WHITE)
            rematchRect = rematchSurface.get_rect()
            rematchRect.center = (screenWidth // 2, screenHeight // 2 + 30)
            screen.blit(rematchSurface, rematchRect)

            # Display which players are ready for the rematch.
            ready1 = latestState.get("rematch_ready1", False)
            ready2 = latestState.get("rematch_ready2", False)

            status1 = "Ready" if ready1 else "Waiting"
            status2 = "Ready" if ready2 else "Waiting"

            readyText = f"P1: {status1}  |  P2: {status2}"

            readySurface = rematchFont.render(readyText, True, WHITE)
            readyRect = readySurface.get_rect()
            readyRect.center = (screenWidth // 2, screenHeight // 2 + 65)
            screen.blit(readySurface, readyRect)
        else:
            # ==== Ball Logic =====================================================================
            # The server controls ball movement, collisions, and scoring.
            # The client only draws the ball at the position received.
            pygame.draw.rect(screen, WHITE, ball.rect)
            # ==== End Ball Logic =================================================================

        # Drawing the dotted line in the center
        for i in centerLine:
            pygame.draw.rect(screen, WHITE, i)

        # Draw both paddles for players and spectators.
        for paddle in [leftPaddle, rightPaddle]:
            pygame.draw.rect(screen, WHITE, paddle)

        pygame.draw.rect(screen, WHITE, topWall)
        pygame.draw.rect(screen, WHITE, bottomWall)
        scoreRect = updateScore(lScore, rScore, screen, WHITE, scoreFont)
        pygame.display.flip()
        clock.tick(60)

        # This number should be synchronized between you and your opponent. If your number is larger,
        # then you are ahead of them in time; if theirs is larger, they are ahead of you, and you need
        # to catch up (use their info).
        sync += 1
        # =========================================================================================
        # Send your server update here at the end of the game loop to sync your game with your
        # opponent's game.
        # The client sends its movement earlier in this loop.
        # Here we check whether the server is still connected.
        if not connectionStatus["connected"]:
            print("Disconnected from the server.")
            running = False
        # =========================================================================================

    pygame.quit()


# This is where you will connect to the server to get the info required to call the game loop.
# Mainly the screen width, height and player paddle (either "left" or "right").
# If you want to hard code the screen's dimensions into the code, that's fine, but you will
# need to know which client is which.
def joinServer(ip: str, port: str, errorLabel: tk.Label, app: tk.Tk, initials: str) -> None:
    # Purpose: This method is fired when the join button is clicked.
    # Arguments:
    # ip: A string holding the IP address of the server.
    # port: A string holding the port the server is using.
    # errorLabel: A tk label widget; modify its text to display messages to the user.
    # app: The tk window object, needed to kill the window.

    # Check initials before connecting so invalid input does not reserve a player slot.
    initials = initials.strip().upper()
    if not (1 <= len(initials) <= 3 and initials.isascii() and initials.isalpha()):
        errorLabel.config(text="Enter 1 to 3 letters for your initials.")
        return

    # Create a socket and connect to the server.
    # You don't have to use SOCK_STREAM; use what you think is best.
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Get the required information from your server (screen width, height & player paddle).
    try:
        client.settimeout(5)
        client.connect((ip.strip(), int(port)))

        # The server sends PLAYER 1 or PLAYER 2.
        player_message = b""
        while not player_message.endswith(b"\n"):
            data = client.recv(1)
            if not data:
                raise ConnectionError("Server disconnected.")
            player_message += data

        player_message = player_message.decode("utf-8").strip()
        if player_message == "PLAYER 1":
            playerPaddle = "left"
        elif player_message == "PLAYER 2":
            playerPaddle = "right"
        elif player_message == "SPECTATOR":
            playerPaddle = "spectator"
        else:
            raise ValueError("Unexpected server response: " + player_message)

        client.settimeout(None)
        if playerPaddle != "spectator":
            client.sendall((json.dumps({"initials": initials}) + "\n").encode("utf-8"))
    except (OSError, ValueError) as error:
        client.close()
        errorLabel.config(text=f"Connection failed: {error}")
        return

    # If you have messages you'd like to show the user, use the errorLabel widget like so.
    errorLabel.config(text=f"Connected as {player_message}")
    # You may or may not need to call this, depending on how many times you update the label.
    errorLabel.update()

    # Close this window and start the game with the info passed to you from the server.
    # app.withdraw()  # Hides the window (we'll kill it later).
    # playGame(screenWidth, screenHeight, ("left"|"right"), client)
    # app.quit()  # Kills the window.
    app.withdraw()
    try:
        playGame(640, 480, playerPaddle, client)
    finally:
        client.close()
        app.destroy()


# This displays the opening screen; you don't need to edit this (but may if you like).
def startScreen():
    app = tk.Tk()
    app.title("Server Info")
    image = tk.PhotoImage(file="./assets/images/logo.png")
    titleLabel = tk.Label(image=image)
    titleLabel.grid(column=0, row=0, columnspan=2)
    ipLabel = tk.Label(text="Server IP:")
    ipLabel.grid(column=0, row=1, sticky="W", padx=8)
    ipEntry = tk.Entry(app)
    ipEntry.grid(column=1, row=1)
    portLabel = tk.Label(text="Server Port:")
    portLabel.grid(column=0, row=2, sticky="W", padx=8)
    portEntry = tk.Entry(app)
    portEntry.grid(column=1, row=2)
    initialsLabel = tk.Label(text="Your Initials:")
    initialsLabel.grid(column=0, row=3, sticky="W", padx=8)
    initialsEntry = tk.Entry(app)
    initialsEntry.grid(column=1, row=3)
    errorLabel = tk.Label(text="")
    errorLabel.grid(column=0, row=5, columnspan=2)
    joinButton = tk.Button(
        text="Join",
        command=lambda: joinServer(ipEntry.get(), portEntry.get(), errorLabel, app, initialsEntry.get())
    )
    joinButton.grid(column=0, row=4, columnspan=2)
    app.mainloop()

if __name__ == "__main__":
    startScreen()

