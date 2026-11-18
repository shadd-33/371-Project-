# =================================================================================================
# Contributing Authors:	    Noella Kule, Jacob Kulig, Shaddai Ngoyi
# Email Addresses:          nku239@uky.edu, jkulig29@uky.edu, Shaddai.Ngoyi@uky.edu
# Date:                     11/18/2026
# Purpose:                  Implements the Pong server, managing client connections, player movements,
#                           ball physics, scoring, and synchronized multiplayer gameplay.
# Misc:                     Uses TCP sockets, JSON, and threading to support two players, unlimited
#                           spectators, and a play-again feature.
# =================================================================================================

import socket
import threading
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from pathlib import Path


# Server configuration
HOST = "0.0.0.0"
PORT = 5555

# Create TCP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allow the port to be reused
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind server to address and port
server.bind((HOST, PORT))

# Listen for incoming connections
server.listen()

print("Server is running...")
print("Waiting for players to connect...")

# Store connected players
clients = []
clients_lock = threading.Lock()
game_running = True
# Track whether both players are ready for another match.
rematch_ready = {
    1: False,
    2: False
}
players_assigned = 0

# Game state
game_state = {
    "paddle1_y": 215,
    "paddle2_y": 215,
    "ball_x": 320,
    "ball_y": 240,
    "score1": 0,
    "score2": 0,
    "sync": 0,
    "winner": None,
    "game_over": False,
    "rematch_ready1": False,
    "rematch_ready2": False
}

ball_dx = -3.5
ball_dy = 0
next_serve_time = 0

# Protect shared game state from simultaneous updates
game_lock = threading.Lock()

# Persistent leaderboard (one win recorded per completed match).
LEADERBOARD_PORT = 80
LEADERBOARD_FILE = Path(__file__).with_name("leaderboard.json")
leaderboard_lock = threading.Lock()
player_initials = {1: "P1", 2: "P2"}

try:
    with LEADERBOARD_FILE.open("r", encoding="utf-8") as file:
        leaderboard = json.load(file)
    if not isinstance(leaderboard, dict):
        leaderboard = {}
except (OSError, ValueError):
    leaderboard = {}


def record_win(player_number):
    initials = player_initials[player_number]
    with leaderboard_lock:
        leaderboard[initials] = leaderboard.get(initials, 0) + 1
        try:
            with LEADERBOARD_FILE.open("w", encoding="utf-8") as file:
                json.dump(leaderboard, file, indent=4)
        except OSError as error:
            print(f"Could not save leaderboard: {error}")
    print(f"Win recorded for {initials}")


class LeaderboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        with leaderboard_lock:
            rankings = sorted(leaderboard.items(), key=lambda item: (-item[1], item[0]))
        rows = "".join(
            f"<tr><td>{rank}</td><td>{escape(name)}</td><td>{wins}</td></tr>"
            for rank, (name, wins) in enumerate(rankings, 1)
        )
        page = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta http-equiv="refresh" content="5">
<title>Pong Leaderboard</title>
<style>
body {{ background:#101827; color:white; font-family:Arial,sans-serif; text-align:center; padding:40px; }}
table {{ margin:auto; border-collapse:collapse; width:min(650px,95%); }}
th,td {{ padding:15px; border-bottom:1px solid #555; }}
th {{ color:#55d6ff; }}
</style></head><body><h1>PONG LEADERBOARD</h1>
<p>Win totals - refreshes every 5 seconds</p>
<table><tr><th>Rank</th><th>Initials</th><th>Wins</th></tr>{rows}</table>
</body></html>"""
        data = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def start_leaderboard():
    try:
        http_server = ThreadingHTTPServer((HOST, LEADERBOARD_PORT), LeaderboardHandler)
        print(f"Leaderboard available on port {LEADERBOARD_PORT}")
        http_server.serve_forever()
    except OSError as error:
        print(f"Leaderboard could not start: {error}")



def handle_client(conn, player_number):

    global game_running
    print(f"Listening for Player {player_number}")

    try:
        with conn.makefile("r", encoding="utf-8") as reader:
            for line in reader:
                message = json.loads(line)
                # Register player initials; spectators do not register.
                if "initials" in message:
                    initials = str(message["initials"]).strip().upper()
                    if 1 <= len(initials) <= 3 and initials.isascii() and initials.isalpha():
                        with game_lock:
                            player_initials[player_number] = initials
                        print(f"Player {player_number} registered as {initials}")
                    continue
                print(f"Received from Player {player_number}: {message}")

                # Check whether this player requested a rematch.
                if message.get("rematch") is True:
                    with game_lock:
                        if game_state["game_over"]:
                            rematch_ready[player_number] = True
                            game_state[f"rematch_ready{player_number}"] = True
                    continue

                direction = message.get("direction")

                if direction not in ("up", "down", "stop"):
                    continue

                paddle = f"paddle{player_number}_y"

                with game_lock:
                    if game_state["game_over"]:
                        continue

                    if direction == "up":
                        game_state[paddle] -= 5
                    elif direction == "down":
                        game_state[paddle] += 5

                    game_state[paddle] = max(
                        10, min(420, game_state[paddle])
                    )

                    game_state["sync"] += 1

                    print(f"Player {player_number} paddle position: {game_state[paddle]}")

    except (OSError, ValueError) as error:
        print(f"Player {player_number} error: {error}")

    finally:
        print(f"Player {player_number} disconnected")

        with game_lock:
            game_running = False

        with clients_lock:
            if conn in clients:
                clients.remove(conn)

        conn.close()


def handle_spectator(conn: socket.socket) -> None:
    print("Listening for spectator disconnect")

    try:
        while game_running:
            data = conn.recv(1024)

            if not data:
                break

    except OSError:
        pass

    finally:
        print("Spectator disconnected")

        with clients_lock:
            if conn in clients:
                clients.remove(conn)

        conn.close()


def broadcast_game_state():
    with game_lock:
        message = json.dumps(game_state) + "\n"

    with clients_lock:
        connected_clients = clients.copy()

    for conn in connected_clients:
        try:
            conn.sendall(message.encode("utf-8"))
        except OSError:
            with clients_lock:
                if conn in clients:
                    clients.remove(conn)

            conn.close()


def reset_game() -> None:
    global ball_dx, ball_dy, next_serve_time

    with game_lock:
        # Reset scores and player positions.
        game_state["score1"] = 0
        game_state["score2"] = 0
        game_state["paddle1_y"] = 215
        game_state["paddle2_y"] = 215

        # Reset the ball.
        game_state["ball_x"] = 320
        game_state["ball_y"] = 240
        ball_dx = -3.5
        ball_dy = 0
        next_serve_time = time.monotonic() + 2

        # Clear the previous winner and rematch requests.
        game_state["winner"] = None
        game_state["game_over"] = False
        game_state["rematch_ready1"] = False
        game_state["rematch_ready2"] = False

        rematch_ready[1] = False
        rematch_ready[2] = False

        game_state["sync"] += 1


def update_ball():
    global ball_dx, ball_dy, next_serve_time

    with game_lock:
        if game_state["score1"] >= 5 or game_state["score2"] >= 5:
            return

        # Pause the ball at the center after a point
        if time.monotonic() < next_serve_time:
            return

        game_state["ball_x"] += ball_dx
        game_state["ball_y"] += ball_dy

        x = game_state["ball_x"]
        y = game_state["ball_y"]

        # Bounce off top and bottom walls
        if y <= 10:
            game_state["ball_y"] = 10
            ball_dy = abs(ball_dy)

        elif y >= 465:
            game_state["ball_y"] = 465
            ball_dy = -abs(ball_dy)

        # Left paddle collision
        if ball_dx < 0 and x <= 20 and x + 5 >= 10:
            paddle_y = game_state["paddle1_y"]

            if y + 5 >= paddle_y and y <= paddle_y + 50:
                game_state["ball_x"] = 20
                ball_dx = abs(ball_dx)
                ball_dy = max(-3, min(3, (y + 2 - (paddle_y + 25)) // 5))

        # Right paddle collision
        elif ball_dx > 0 and x + 5 >= 620 and x <= 630:
            paddle_y = game_state["paddle2_y"]

            if y + 5 >= paddle_y and y <= paddle_y + 50:
                game_state["ball_x"] = 615
                ball_dx = -abs(ball_dx)
                ball_dy = max(-3, min(3, (y + 2 - (paddle_y + 25)) // 5))

        # Scoring
        if x > 640:
            game_state["score1"] += 1
            game_state["ball_x"] = 320
            game_state["ball_y"] = 240
            ball_dx = -3.5
            ball_dy = 0
            next_serve_time = time.monotonic() + 2

        elif x < 0:
            game_state["score2"] += 1
            game_state["ball_x"] = 320
            game_state["ball_y"] = 240
            ball_dx = 3.5
            ball_dy = 0
            next_serve_time = time.monotonic() + 2

        # Record exactly one win per match, including after rematches.
        if not game_state["game_over"]:
            if game_state["score1"] >= 5:
                game_state["winner"] = 1
                game_state["game_over"] = True
                record_win(1)
            elif game_state["score2"] >= 5:
                game_state["winner"] = 2
                game_state["game_over"] = True
                record_win(2)

        game_state["sync"] += 1

def run_game():
    print("Both players connected!")
    print("Game is ready to start!")

    while game_running:
        # Check whether both players requested a rematch.
        with game_lock:
            start_rematch = (
                game_state["game_over"]
                and rematch_ready[1]
                and rematch_ready[2]
            )

        if start_rematch:
            print("Both players are ready! Starting a new match.")
            reset_game()

        update_ball()
        broadcast_game_state()
        time.sleep(1 / 60)


# Serve leaderboard in a separate thread alongside the Pong TCP server.
threading.Thread(target=start_leaderboard, daemon=True).start()

# Accept two players
server.settimeout(1.0)

while game_running:
    try:
        conn, addr = server.accept()
    except socket.timeout:
        continue

    with clients_lock:
        clients.append(conn)

        if players_assigned < 2:
            players_assigned += 1
            player_number = players_assigned
        else:
            player_number = None

    if player_number is not None:
        print(f"Player {player_number} connected from {addr}")
        conn.sendall(f"PLAYER {player_number}\n".encode())

        threading.Thread(
            target=handle_client,
            args=(conn, player_number),
            daemon=True
        ).start()

        if player_number == 2:
            game_thread = threading.Thread(
                target=run_game,
                daemon=True
            )
            game_thread.start()
    else:
        print(f"Spectator connected from {addr}")
        conn.sendall(b"SPECTATOR\n")

        threading.Thread(
            target=handle_spectator,
            args=(conn,),
            daemon=True
        ).start()

if not game_running:
    print("A player disconnected before the game started.")
    with clients_lock:
        remaining_clients = clients.copy()

    for conn in remaining_clients:
        conn.close()

    server.close()
    raise SystemExit


print("Game stopped.")

# Close all remaining player connections
with clients_lock:
    remaining_clients = clients.copy()
    clients.clear()

for conn in remaining_clients:
    try:
        conn.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass

    conn.close()

# Close the server socket
server.close()

print("Server shut down successfully.")
