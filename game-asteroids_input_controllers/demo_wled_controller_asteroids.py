import pygame
import sys
import asyncio
import aiohttp
import time
import threading
import numpy as np
import random
import os
from dotenv import load_dotenv

# v7
# - add reset on game over

# v8
# - disable sound ( hardware is to slow :( )
# - add waiting effect on start game

# v9
# - effects stopping at the spaceship, (SPACE_POS)
# - added env: SPACEPOS -> SPACE_POS, fallback: 0
# - added env: LEDCOUNT -> LED_COUNT, fallback: 250

# --- SOUND CONFIGURATION ---
# pygame.mixer.init(frequency=44100, size=-16, channels=1)

def create_tone(frequency, duration):
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    if frequency == 0:
        samples = np.zeros(num_samples, dtype=np.int16)
    else:
        t = np.linspace(0, duration, num_samples, False)
        wave = 0.5 * np.sin(2 * np.pi * frequency * t)
        samples = np.int16(wave * 32767)
    sound = pygame.sndarray.make_sound(samples)
    return sound

def start_sfx(sequence):
    for freq, dur in sequence:
        sound = create_tone(freq, dur)
        sound.play()
        pygame.time.wait(int(dur * 1000))

def play_shot():
    start_sfx([(1500, 0.02), (1300, 0.02), (1100, 0.02), (900, 0.04)])

# --- CONFIG ---
env_path = '/opt/games/.env'

# Default values
DEFAULT_WLED_IP = '127.0.0.1'
DEFAULT_SPACE_POS = 0
DEFAULT_LED_COUNT = 250

# Initialize variables
WLED_IP = DEFAULT_WLED_IP
SPACE_POS = DEFAULT_SPACE_POS
LED_COUNT = DEFAULT_LED_COUNT

if os.path.isfile(env_path):
    load_dotenv(env_path)
    print("Environment variables loaded from", env_path)

    # WLED IP
    WLED_IP = os.getenv('WLEDIP', DEFAULT_WLED_IP)
    print("Value of WLED_IP:", WLED_IP)

    # SPACE POS
    space_pos_str = os.getenv('SPACEPOS')
    if space_pos_str:
        try:
            SPACE_POS = int(space_pos_str)
            print("Value of SPACE_POS:", SPACE_POS)
        except ValueError:
            print(f"Invalid SPACEPOS value '{space_pos_str}', defaulting to {DEFAULT_SPACE_POS}")
            SPACE_POS = DEFAULT_SPACE_POS
    else:
        print(f"SPACEPOS is not set in the environment, defaulting to {DEFAULT_SPACE_POS}")

    # LED COUNT
    led_count_str = os.getenv('LEDCOUNT')
    if led_count_str:
        try:
            LED_COUNT = int(led_count_str)
            print("Value of LED_COUNT:", LED_COUNT)
        except ValueError:
            print(f"Invalid LEDCOUNT value '{led_count_str}', defaulting to {DEFAULT_LED_COUNT}")
            LED_COUNT = DEFAULT_LED_COUNT
    else:
        print(f"LEDCOUNT is not set in the environment, defaulting to {DEFAULT_LED_COUNT}")

else:
    print("No .env file found at", env_path)
    print(f"Using default values: WLED_IP={WLED_IP}, SPACE_POS={SPACE_POS}, LED_COUNT={LED_COUNT}")

# --- WLED CONFIG ---
WLED_URL = f"http://{WLED_IP}/json/state"

pygame.init()
pygame.joystick.init()

# Wait until a joystick is connected
while pygame.joystick.get_count() == 0:
    print("❌ Nx controller detected! Please plug one in.")
    time.sleep(1)
    pygame.joystick.quit()
    pygame.joystick.init()

# init
controller = pygame.joystick.Joystick(0)
controller.init()
print(f"🎮 Connected to: {controller.get_name()}")

# Button mapping
XBOX_BUTTON_MAP = {
    0: "A Button",
    1: "B Button",
    2: "X Button",
    3: "Y Button",
    4: "Left Bumper (LB)",
    5: "Right Bumper (RB)",
    6: "Back / View Button",
    7: "Start / Menu Button",
    8: "Xbox Guide Button",
    9: "Left Stick Click (RSB)",
    10: "Right Stick Click (RSB)"
}

PS4_BUTTON_MAP = {
    0: "X Button (X)",
    1: "● Button (O)",
    2: "■ Button",
    3: "▲ Button",
    4: "Share Button",
    5: "PS Guide Button",
    6: "Options Button",
    7: "(joystick) Left Stick Click",
    8: "(joystick) Right Stick Click",
    9: "Left Bumper",
    10: "Right Bumper",
    11: "up",
    12: "down",
    13: "left",
    14: "right",
    15: "PAD Button"
}

# Detect controller type
controller_name_lower = controller.get_name().lower()

if "dualshock" in controller_name_lower or "ps4 controller" in controller_name_lower:
    BUTTON_X = 2
    BUTTON_Y = 3
    BUTTON_A = 0
    BUTTON_B = 1
    BUTTON_START = 5
    BUTTON_MAP = PS4_BUTTON_MAP
    print("🕹️  Detected PS4 DualShock Controller")
else:
    BUTTON_X = 2
    BUTTON_Y = 3
    BUTTON_A = 0
    BUTTON_B = 1
    BUTTON_START = 8
    BUTTON_MAP = XBOX_BUTTON_MAP
    print("🕹️ Detected Xbox Controller")

# GAME CONFIG
COLOR_MAP = {
    BUTTON_X: [0, 0, 255],    # Blue
    BUTTON_Y: [255, 255, 0],  # Yellow
    BUTTON_B: [255, 0, 0],    # Red
    BUTTON_A: [0, 255, 0],    # Green
}

LIVES = 3
GAME_OVER = False
#SPACE_POS = 26
#SPACE_POS = 0
#LED_COUNT = 50

# Asteroid parameters
ASTEROID_INTERVAL = 4.0
ASTEROID_COLORS = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0]]
asteroids = []

bullets = []

# Spaceship LED positions (indicate lives)
spaceship_leds = [SPACE_POS, SPACE_POS + 1, SPACE_POS + 2]

# Async event loop for sending LEDs
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def send_leds(led_array):
    payload = {
        "on": True,
        "bri": 95,
        "seg": {"id": 0, "i": led_array}
    }
    async def _send():
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(WLED_URL, json=payload, timeout=0.2)
        except:
            pass
    asyncio.run_coroutine_threadsafe(_send(), loop)

def start_loop():
    print("INFO: Starting asyncio loop.")
    loop.run_forever()

threading.Thread(target=start_loop, daemon=True).start()

def draw_game():
    led_array = [[0, 0, 0] for _ in range(LED_COUNT)]
    # Draw spaceship lives indicator
    for i, led_pos in enumerate(spaceship_leds):
        if i < LIVES:
            led_array[led_pos] = [255, 255, 255]
        else:
            led_array[led_pos] = [0, 0, 0]
    # Draw asteroids
    for ast in asteroids:
        if 0 <= ast['pos'] < LED_COUNT:
            led_array[ast['pos']] = ast['color']
    # Draw bullets
    for bul in bullets:
        if 0 <= bul['pos'] < LED_COUNT:
            led_array[bul['pos']] = bul['color']
    send_leds(led_array)

def blink_all(led_array):
    for _ in range(3):
        #for i in range(LED_COUNT):
        for i in range(SPACE_POS, LED_COUNT):
            led_array[i] = [255, 255, 255]
        send_leds(led_array)
        time.sleep(0.2)
        #for i in range(LED_COUNT):
        for i in range(SPACE_POS, LED_COUNT):
            led_array[i] = [0, 0, 0]
        send_leds(led_array)
        time.sleep(0.2)

def fade_in_out(led_array, color, duration=2.0, steps=50):
    """
    Fade in and out the LED strip starting from the end towards SPACE_POS.
    """
    step_delay = duration / (2 * steps)
    for i in range(steps):
        brightness = (i + 1) / steps
        for j in range(SPACE_POS, LED_COUNT):
            led_array[j] = [int(c * brightness) for c in color]
        send_leds(led_array)
        time.sleep(step_delay)
    for i in range(steps):
        brightness = 1 - (i + 1) / steps
        for j in range(SPACE_POS, LED_COUNT):
            led_array[j] = [int(c * brightness) for c in color]
        send_leds(led_array)
        time.sleep(step_delay)

# --- Waiting for start effect (non-blocking) ---
waiting_for_start = True
fade_step_counter = 0
fade_direction = 1  # 1 for fade in, -1 for fade out
fade_steps = 25
# Initialize LED array for wait effect
wait_led_array = [[0, 0, 0] for _ in range(LED_COUNT)]
print("🚀 Waiting for start! Press Start button to begin...")

# Main game loop
while True:
    events = pygame.event.get()

    if waiting_for_start:
        # Run non-blocking fade in/out effect
        fade_step_counter += 1
        if fade_step_counter >= fade_steps:
            fade_step_counter = 0
            fade_direction *= -1  # toggle direction

        # Calculate brightness based on fade direction
        if fade_direction == 1:
            brightness = (fade_step_counter + 1) / fade_steps
        else:
            brightness = 1 - (fade_step_counter + 1) / fade_steps

        # Apply brightness to the LED array
#        for i in range(LED_COUNT):
#            wait_led_array[i] = [int(c * brightness) for c in [0, 0, 255]]  # blue color

        for i in range(SPACE_POS, LED_COUNT):
            wait_led_array[i] = [int(c * brightness) for c in [0, 0, 255]]  # blue color

        send_leds(wait_led_array)

        # Check for start button press
        for event in events:
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == BUTTON_START:
                    print("Start button pressed. Starting game...")
                    waiting_for_start = False
                    break

        time.sleep(0.1)
        continue

    # Main game logic after start
    # Spawn asteroids periodically
    if 'last_asteroid_time' not in locals():
        last_asteroid_time = time.time()

    current_time = time.time()

    # Spawn asteroid
    if current_time - last_asteroid_time > ASTEROID_INTERVAL:
        spawn_color = random.choice(ASTEROID_COLORS)
        asteroids.append({'pos': LED_COUNT - 1, 'color': spawn_color})
        last_asteroid_time = current_time

    # Save previous positions for collision detection
    prev_asteroids_positions = [ast['pos'] for ast in asteroids]
    prev_bullets_positions = [b['pos'] for b in bullets]

    # Move asteroids down
    for ast in asteroids:
        ast['pos'] -= 1
    asteroids = [a for a in asteroids if a['pos'] >= 0]

    # Move bullets up
    for b in bullets:
        b['pos'] += 1
    bullets = [b for b in bullets if b['pos'] < LED_COUNT]

    # Draw LEDs
    draw_game()

    # Handle input events
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.JOYBUTTONDOWN:
            btn = event.button
            btn_name = BUTTON_MAP.get(btn, f"Button {btn}")
            print(f"DEBUG: {btn_name} pressed.")
            if btn == BUTTON_START:
                print("Game started by start button.")
                waiting_for_start = False
            elif btn in COLOR_MAP:
                # Fire bullet
                bullets.append({'pos': SPACE_POS + 2, 'color': COLOR_MAP[btn]})
                #play_shot()

    # Collision detection between bullets and asteroids
    for bul in bullets[:]:
        for ast in asteroids[:]:
            prev_ast_pos = None
            prev_bul_pos = None
            try:
                prev_ast_pos = prev_asteroids_positions[asteroids.index(ast)]
            except:
                prev_ast_pos = None
            try:
                prev_bul_pos = prev_bullets_positions[bullets.index(bul)]
            except:
                prev_bul_pos = None

            collision = False
            if prev_ast_pos is not None and prev_bul_pos is not None:
                if (prev_ast_pos >= prev_bul_pos and ast['pos'] <= bul['pos']) or \
                   (prev_bul_pos >= prev_ast_pos and bul['pos'] <= ast['pos']):
                    collision = True
            else:
                if ast['pos'] == bul['pos']:
                    collision = True

            if collision:
                if ast['color'] == bul['color']:
                    if ast in asteroids:
                        asteroids.remove(ast)
                    if bul in bullets:
                        bullets.remove(bul)
                else:
                    LIVES -= 1
                    # Update LEDs
                    led_array = [[0,0,0] for _ in range(LED_COUNT)]
                    for i, led_pos in enumerate(spaceship_leds):
                        if i < LIVES:
                            led_array[led_pos] = [255, 255, 255]
                        else:
                            led_array[led_pos] = [0, 0, 0]
                    send_leds(led_array)
                    blink_all(led_array)
                    if bul in bullets:
                        bullets.remove(bul)
                    print(f"Lives remaining: {LIVES}")
                    if LIVES <= 0:
                        print("GAME OVER! Resetting game.")
                        LIVES = 3
                        asteroids.clear()
                        bullets.clear()
                        waiting_for_start = True
                        break

    # Check asteroid hits spaceship
    for ast in asteroids[:]:
        if ast['pos'] == SPACE_POS:
            LIVES -= 1
            led_array = [[0,0,0] for _ in range(LED_COUNT)]
            for i, led_pos in enumerate(spaceship_leds):
                if i < LIVES:
                    led_array[led_pos] = [255, 255, 255]
                else:
                    led_array[led_pos] = [0, 0, 0]
            send_leds(led_array)
            blink_all(led_array)
            asteroids.remove(ast)
            print(f"Asteroid hit! Lives remaining: {LIVES}")
            if LIVES <= 0:
                print("GAME OVER! Resetting game.")
                LIVES = 3
                asteroids.clear()
                bullets.clear()
                waiting_for_start = True
                break

    # If game over, wait for start again
    if LIVES <= 0:
        waiting_for_start = True

    time.sleep(0.1)
