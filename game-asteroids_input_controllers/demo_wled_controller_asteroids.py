import pygame
import sys
import asyncio
import aiohttp
import time
import threading
import numpy as np
import random

# v5

# --- SOUND CONFIGURATION ---
pygame.mixer.init(frequency=44100, size=-16, channels=1)

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

# --- WLED CONFIG ---
WLED_IP = "10.0.0.101"  # Change as needed
WLED_URL = f"http://{WLED_IP}/json/state"

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("❌ No Xbox controller detected! Please plug one in.")
    sys.exit()

controller = pygame.joystick.Joystick(0)
controller.init()
print(f"🎮 Connected to: {controller.get_name()}")

# Button mapping
BUTTON_X = 2
BUTTON_Y = 3
BUTTON_A = 0
BUTTON_B = 1
BUTTON_START = 7

BUTTON_MAP = {
    0: "A",
    1: "B",
    2: "X",
    3: "Y",
    7: "Start"
}

COLOR_MAP = {
    BUTTON_X: [0, 0, 255],    # Blue
    BUTTON_Y: [255, 255, 0],  # Yellow
    BUTTON_B: [255, 0, 0],    # Red
    BUTTON_A: [0, 255, 0],    # Green
}

LIVES = 3
GAME_OVER = False
SPACE_POS = 0
LED_COUNT = 50

# Asteroid parameters
ASTEROID_INTERVAL = 4.0
ASTEROID_COLORS = [[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 0]]
asteroids = []

bullets = []

# Spaceship LED positions (indicate lives)
# Define spaceship LED positions based on SPACE_POS
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
        # Blink all LEDs white
        for i in range(LED_COUNT):
            led_array[i] = [255, 255, 255]
        send_leds(led_array)
        time.sleep(0.2)
        # Turn off all LEDs
        for i in range(LED_COUNT):
            led_array[i] = [0, 0, 0]
        send_leds(led_array)
        time.sleep(0.2)

# Main game loop
last_asteroid_time = time.time()

print("🚀 Starting game! Press Y/X/A/B to fire, Start to start game...")

prev_asteroids_positions = []
prev_bullets_positions = []

while True:
    current_time = time.time()
    events = pygame.event.get()

    # Spawn asteroids
    if current_time - last_asteroid_time > ASTEROID_INTERVAL:
        spawn_color = random.choice(ASTEROID_COLORS)
        asteroids.append({'pos': LED_COUNT - 1, 'color': spawn_color})
        last_asteroid_time = current_time

    # Save previous positions
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
                print("🟢 Game started!")
                LIVES = 3
                GAME_OVER = False
                asteroids.clear()
                bullets.clear()
            elif btn in COLOR_MAP:
                # Fire bullet
                bullets.append({'pos': SPACE_POS + 2, 'color': COLOR_MAP[btn]})
                play_shot()

    # Collision detection with path crossing
    for bul in bullets[:]:
        for ast in asteroids[:]:
            prev_ast_pos = None
            prev_bul_pos = None
            # Find previous positions
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
                # Check if path crossed
                if (prev_ast_pos >= prev_bul_pos and ast['pos'] <= bul['pos']) or \
                   (prev_bul_pos >= prev_ast_pos and bul['pos'] <= ast['pos']):
                    collision = True
            else:
                # If no previous data, check current positions
                if ast['pos'] == bul['pos']:
                    collision = True

            if collision:
                if ast['color'] == bul['color']:
                    # Destroy both
                    if ast in asteroids:
                        asteroids.remove(ast)
                    if bul in bullets:
                        bullets.remove(bul)
                else:
                    # Miss: deduct life, blink, remove a spaceship LED
                    LIVES -= 1
                    # Draw current lives
                    led_array = [[0,0,0] for _ in range(LED_COUNT)]
                    for i, led_pos in enumerate(spaceship_leds):
                        if i < LIVES:
                            led_array[led_pos] = [255, 255, 255]
                        else:
                            led_array[led_pos] = [0, 0, 0]
                    send_leds(led_array)
                    blink_all(led_array)
                    # Remove bullet
                    if bul in bullets:
                        bullets.remove(bul)
                    print(f"Lives remaining: {LIVES}")
                    if LIVES <= 0:
                        print("GAME OVER! You lost all lives.")
                        pygame.quit()
                        sys.exit()

    # Check if any asteroid hits the spaceship
    for ast in asteroids[:]:
        if ast['pos'] == SPACE_POS:
            # Asteroid hit spaceship
            LIVES -= 1
            # Draw current lives
            led_array = [[0,0,0] for _ in range(LED_COUNT)]
            for i, led_pos in enumerate(spaceship_leds):
                if i < LIVES:
                    led_array[led_pos] = [255, 255, 255]
                else:
                    led_array[led_pos] = [0, 0, 0]
            send_leds(led_array)
            blink_all(led_array)
            # Remove asteroid
            asteroids.remove(ast)
            print(f"Asteroid hit! Lives remaining: {LIVES}")
            if LIVES <= 0:
                print("GAME OVER! You lost all lives.")
                pygame.quit()
                sys.exit()

    # End game if lives exhausted
    if LIVES <= 0:
        break

    time.sleep(0.1)
