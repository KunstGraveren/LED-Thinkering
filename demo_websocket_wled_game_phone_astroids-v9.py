import asyncio
import json
import random
import http.server
import socketserver
import threading
import math
import sys
import websockets
import aiohttp

# --- HARDWARE & GAME CONFIGURATION ---
#WLED_IP = "10.20.0.111"  # Update with your WLED device IP -- RED
#WLED_IP = "10.20.0.117"  # Update with your WLED device IP -- BLUE
WLED_IP = "10.20.0.118"  # Update with your WLED device IP -- GREEN
#WLED_IP = "192.168.178.160"  # Update with your WLED device IP -- GREEN
WLED_URL = f"http://{WLED_IP}/json/state"
NUM_LEDS = 100  # Number of pixels on your strip

# --- FIXED SUB-TICK RESOLUTION ---
LOOP_TICK_RATE = 0.03  # Loop cycle time (30ms)

# --- ENGINE SPEED (Asteroid Movement Timers) ---
BASE_ASTEROID_DELAY = 0.12     # Level 1 asteroid move delay (120ms)
SPEED_DECREASE_PER_LEVEL = 0.005
MIN_ASTEROID_DELAY = 0.04

# --- COLOR PATTERNS (RGB) ---
COLOR_OFF = [0, 0, 0]
COLOR_SHIP = [255, 255, 255]
COLOR_BOOM = [255, 255, 255]

COLORS_MAP = {
    0: {"name": "Cyan",    "rgb": [0, 255, 255]},
    1: {"name": "Yellow",  "rgb": [255, 255, 0]},
    2: {"name": "Red",     "rgb": [255, 0, 0]},
    3: {"name": "Green",   "rgb": [0, 255, 0]},
    4: {"name": "Magenta", "rgb": [255, 0, 255]}
}

class GameEngine:
    def __init__(self):
        self.is_started = False
        self.ship_pos = 0
        self.lasers = []  # list of dicts: {"pos": int, "color_id": int}
        self.rocks = []   # list of dicts: {"pos": int, "color_id": int}
        self.explosions = {}  # dict: {index: remaining_frames}
        self.score = 0
        self.game_over = False
        self.connected_sockets = set()
        self.pulse_frame = 0

        # Level & Wave Management
        self.level = 1
        self.max_levels = 99
        self.asteroid_delay = BASE_ASTEROID_DELAY
        self.asteroid_timer = 0.0

        self.wave_active = False
        self.rocks_left_to_spawn_this_wave = 0
        self.waves_completed_in_level = 0
        self.total_waves_required_for_level = 3

    def reset(self):
        print("[DEBUG ENGINE] Resetting game state.")
        saved_sockets = self.connected_sockets
        self.__init__()
        self.connected_sockets = saved_sockets
        self.broadcast_state_instantly()

    def start_game(self):
        print("[DEBUG ENGINE] Game started!")
        self.is_started = True
        self.start_new_wave()

    def start_new_wave(self):
        self.wave_active = True
        self.rocks_left_to_spawn_this_wave = 5 + (self.level * 2)

    def advance_level(self):
        if self.level < self.max_levels:
            self.level += 1
            self.asteroid_delay = max(
                MIN_ASTEROID_DELAY,
                BASE_ASTEROID_DELAY - (self.level * SPEED_DECREASE_PER_LEVEL)
            )
            self.waves_completed_in_level = 0
            self.total_waves_required_for_level = 3 + (self.level // 2)
        else:
            print("[DEBUG ENGINE] Max level reached!")

    def fire_laser(self, color_id):
        if self.is_started and not self.game_over:
            if not any(l["pos"] == self.ship_pos + 1 and l["color_id"] == color_id for l in self.lasers):
                self.lasers.append({"pos": self.ship_pos + 1, "color_id": color_id})

    def broadcast_state_instantly(self):
        """Send immediate out-of-band state update to all connected sockets."""
        if self.connected_sockets:
            msg = json.dumps({
                'score': self.score,
                'game_over': self.game_over,
                'is_started': self.is_started,
                'level': self.level
            })
            for ws in list(self.connected_sockets):
                try:
                    asyncio.get_event_loop().create_task(ws.send(msg))
                except Exception:
                    pass

    def tick(self):
        if not self.is_started:
            self.pulse_frame = (self.pulse_frame + 1) % 360
            return
        if self.game_over:
            return

        # 1. Advance lasers
        for l in self.lasers:
            l["pos"] += 1
        self.lasers = [l for l in self.lasers if l["pos"] < NUM_LEDS]

        # 2. Asteroid movement timing (decoupled)
        self.asteroid_timer += LOOP_TICK_RATE
        if self.asteroid_timer >= self.asteroid_delay:
            self.asteroid_timer = 0.0

            far_edge = NUM_LEDS - 1
            is_spawning_slot_clear = not any(r["pos"] == far_edge for r in self.rocks)

            if self.wave_active and self.rocks_left_to_spawn_this_wave > 0:
                if is_spawning_slot_clear:
                    rand_color = random.randint(0, 4)
                    self.rocks.append({"pos": far_edge, "color_id": rand_color})
                    self.rocks_left_to_spawn_this_wave -= 1
                    if self.rocks_left_to_spawn_this_wave <= 0:
                        self.wave_active = False

            for r in self.rocks:
                r["pos"] -= 1

        # 3. Collision detection
        hit_lasers = []
        hit_rocks = []
        for l in self.lasers:
            for r in self.rocks:
                if l["pos"] == r["pos"] or l["pos"] == r["pos"] + 1:
                    if l["color_id"] == r["color_id"]:
                        hit_lasers.append(l)
                        hit_rocks.append(r)
                        self.explosions[r["pos"]] = 2
                        self.score += 10
        self.lasers = [l for l in self.lasers if l not in hit_lasers]
        self.rocks = [r for r in self.rocks if r not in hit_rocks]

        for idx in list(self.explosions.keys()):
            self.explosions[idx] -= 1
            if self.explosions[idx] <= 0:
                del self.explosions[idx]

        # 4. Wave/Level progression
        if not self.wave_active and len(self.rocks) == 0:
            self.waves_completed_in_level += 1
            if self.waves_completed_in_level >= self.total_waves_required_for_level:
                self.advance_level()
            self.start_new_wave()

        # 5. Crash condition
        if any(r["pos"] <= 0 for r in self.rocks):
            self.game_over = True

    def build_led_payload(self):
        led_strip = [COLOR_OFF] * NUM_LEDS
        if not self.is_started:
            brightness = int((math.sin(math.radians(self.pulse_frame * 8)) + 1) * 60) + 15
            for i in range(NUM_LEDS):
                led_strip[i] = [0, brightness // 2, brightness]
            return led_strip

        for r in self.rocks:
            if 0 <= r["pos"] < NUM_LEDS:
                led_strip[r["pos"]] = COLORS_MAP[r["color_id"]]["rgb"]
        for l in self.lasers:
            if 0 <= l["pos"] < NUM_LEDS:
                led_strip[l["pos"]] = COLORS_MAP[l["color_id"]]["rgb"]
        for idx in self.explosions:
            if 0 <= idx < NUM_LEDS:
                led_strip[idx] = COLOR_BOOM

        # Draw the ship
        if 0 <= self.ship_pos < NUM_LEDS:
            led_strip[self.ship_pos] = COLOR_SHIP

        return led_strip

game = GameEngine()

# --- WEB INTERFACE (HTML + JS) ---
HTML_UI = """<!DOCTYPE html>
<html>
<head>
    <title>1D Color Asteroids</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <style>
        body { background: #11141a; color: #fff; font-family: 'Courier New', monospace; text-align: center; margin: 0; padding: 20px; }
        .container { max-width: 90%; margin: auto; padding-top: 3vh; }
        h1 { color: #ffffff; font-size: 2rem; margin-bottom: 2px; letter-spacing: 2px; }
        /* Remove title in landscape mode, hide h1 */
        @media (orientation: landscape) {
            h1 { display: none; }
        }
        #level-indicator { font-size: 1.2rem; color: #00ff88; font-weight: bold; margin-bottom: 10px; display: inline-block; }
        #score-board { font-size: 3.5rem; font-weight: bold; margin: 10px 0; color: #ffff00; text-shadow: 0 0 10px rgba(255,255,0,0.4); display: inline-block; }
        /* Style for level and score container in landscape */
        #level-score-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
        }
        .btn { width: 100%; max-width: 90%; height: 60px; font-size: 1.4rem; font-weight: bold; border: none; border-radius: 15px; cursor: pointer; text-transform: uppercase; box-shadow: 0 8px 20px rgba(0,0,0,0.5); margin: 8px auto; transition: transform 0.05s; -webkit-tap-highlight-color: transparent; display: block; }
        .btn:active { transform: scale(0.95); }
        #start-btn { background: linear-gradient(135deg, #00ff88, #0099ff); color: #000; display: block; }
        #reset-btn { background: #333; color: #aaa; display: none; height: 50px; font-size: 1.2rem; }
        .weapon-rack { display: none; flex-direction: column; align-items: center; width: 100%; }
        /* Style buttons for landscape to be inline with colors preserved */
        @media (orientation: landscape) {
            .weapon-rack { flex-direction: row; flex-wrap: wrap; justify-content: center; }
            .w-btn { height: 50px; font-size: 1.2rem; margin: 4px; width: auto; min-width: 100px; max-width: 150px; }
        }
        /* Make buttons responsive for small screens */
        @media(max-width: 400px) {
            .btn { height: 50px; font-size: 1.2rem; }
            .w-btn { height: 45px; font-size: 1.1rem; }
        }
        /* Additional styling for buttons in portrait mode (default) */
        @media (orientation: portrait) {
            .weapon-rack { flex-direction: column; }
            .w-btn { width: 100%; }
        }
        /* Preserve specific button colors (no override) */
        #btn-cyan { background: #00ffff; box-shadow: 0 0 15px rgba(0,255,255,0.4); }
        #btn-yellow { background: #ffff00; box-shadow: 0 0 15px rgba(255,255,0,0.4); }
        #btn-red { background: #ff3333; color: #fff; box-shadow: 0 0 15px rgba(255,51,51,0.4); }
        #btn-green { background: #00ff00; box-shadow: 0 0 15px rgba(0,255,0,0.4); }
        #btn-magenta { background: #ff00ff; color: #fff; box-shadow: 0 0 15px rgba(255,0,255,0.4); }
    </style>
</head>
<body>
    <div class="container">
        <!-- Remove the main title in landscape mode -->
        <h1>1D Asteroids</h1>
        <!-- Container for level and score side by side in landscape -->
        <div id="level-score-container">
            <div id="level-indicator">LEVEL 01</div>
            <div id="score-board">0000</div>
        </div>
        <div id="status">INITIALIZING SYSTEMS...</div>
        <button id="start-btn" class="btn" onclick="sendCmd('START')">START MISSION</button>
        <div id="weapon-rack" class="weapon-rack">
            <button id="btn-cyan"    class="btn w-btn" onclick="sendCmd('FIRE_0')">Cyan Strike</button>
            <button id="btn-yellow"  class="btn w-btn" onclick="sendCmd('FIRE_1')">Yellow Strike</button>
            <button id="btn-red"     class="btn w-btn" onclick="sendCmd('FIRE_2')">Red Strike</button>
            <button id="btn-green"   class="btn w-btn" onclick="sendCmd('FIRE_3')">Green Strike</button>
            <button id="btn-magenta" class="btn w-btn" onclick="sendCmd('FIRE_4')">Magenta Strike</button>
        </div>
        <button id="reset-btn" class="btn" onclick="sendCmd('RESET')">Restart Mission</button>
    </div>
    <script>
        const ws = new WebSocket("ws://" + window.location.hostname + ":8001");
        const statusDiv = document.getElementById("status");
        const scoreBoard = document.getElementById("score-board");
        const levelIndicator = document.getElementById("level-indicator");
        const startBtn = document.getElementById("start-btn");
        const weaponRack = document.getElementById("weapon-rack");
        const resetBtn = document.getElementById("reset-btn");

        ws.onopen = () => statusDiv.innerText = "LOCAL NETWORK ONLINE";
        ws.onclose = () => statusDiv.innerText = "LOCAL CONNECTION LOST";

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            scoreBoard.innerText = String(data.score).padStart(4, '0');
            levelIndicator.innerText = "LEVEL " + String(data.level).padStart(2, '0');

            if (data.game_over) {
                statusDiv.innerText = "GAME OVER - DEFENSES BREACHED";
                statusDiv.style.color = "#ff0000";
                weaponRack.style.display = "none";
                startBtn.style.display = "none";
                resetBtn.style.display = "block";
            } else if (data.is_started) {
                statusDiv.style.color = "#00ffff";
                statusDiv.innerText = "MATCH COLORS TO DESTROY TARGETS";
                startBtn.style.display = "none";
                resetBtn.style.display = "none";
                weaponRack.style.display = "flex";
            } else {
                statusDiv.style.color = "#666";
                statusDiv.innerText = "READY FOR COMBAT CAPTAIN";
                weaponRack.style.display = "none";
                resetBtn.style.display = "none";
                startBtn.style.display = "block";
            }
        };

        function sendCmd(payload) {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(payload);
            }
        }

        const bindings = [
            { id: 'start-btn', cmd: 'START' },
            { id: 'reset-btn', cmd: 'RESET' },
            { id: 'btn-cyan', cmd: 'FIRE_0' },
            { id: 'btn-yellow', cmd: 'FIRE_1' },
            { id: 'btn-red', cmd: 'FIRE_2' },
            { id: 'btn-green', cmd: 'FIRE_3' },
            { id: 'btn-magenta', cmd: 'FIRE_4' }
        ];

        bindings.forEach(item => {
            const el = document.getElementById(item.id);
            if (el) {
                el.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    sendCmd(item.cmd);
                });
            }
        });
    </script>
</body>
</html>
"""

# --- FIXED HIGH-AVAILABILITY HTTP THREAD SERVER ---
class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Creates an independent thread for each client connection."""
    allow_reuse_address = True

class PureHTTPServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(HTML_UI.encode("utf-8"))

    def log_message(self, format, *args):
        pass

def run_http_server():
    with ThreadedHTTPServer(("0.0.0.0", 8000), PureHTTPServer) as httpd:
        httpd.serve_forever()

# --- ASYNC WEBSOCKET & GAME LOOP ---
async def wled_worker():
    async with aiohttp.ClientSession() as session:
        while True:
            game.tick()
            led_colors = game.build_led_payload()
            payload = {
                "on": True,
                "bri": 32,
                "seg": {"id": 0, "i": led_colors}
            }
            try:
                await session.post(WLED_URL, json=payload, timeout=0.05)
            except:
                pass

            # Broadcast current game state to all connected clients
            if game.connected_sockets:
                msg = json.dumps({
                    'score': game.score,
                    'game_over': game.game_over,
                    'is_started': game.is_started,
                    'level': game.level
                })
                connections = list(game.connected_sockets)
                await asyncio.gather(*[ws.send(msg) for ws in connections], return_exceptions=True)

            await asyncio.sleep(LOOP_TICK_RATE)

async def ws_handler(websocket):
    game.connected_sockets.add(websocket)
    # Send current game state immediately upon connection
    initial_msg = json.dumps({
        'score': game.score,
        'game_over': game.game_over,
        'is_started': game.is_started,
        'level': game.level
    })
    try:
        await websocket.send(initial_msg)
        async for message in websocket:
            if message == "START":
                game.start_game()
            elif message == "RESET":
                game.reset()
            elif message.startswith("FIRE_"):
                try:
                    color_index = int(message.split("_")[1])
                    game.fire_laser(color_index)
                except (IndexError, ValueError):
                    pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        game.connected_sockets.remove(websocket)

async def main():
    threading.Thread(target=run_http_server, daemon=True).start()
    print("Multi-threaded web server active at http://localhost:8000")
    asyncio.create_task(wled_worker())
    async with websockets.serve(ws_handler, "0.0.0.0", 8001):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)


