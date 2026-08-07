import pygame
import sys
import asyncio
import aiohttp
import time
import threading

# --- SOUND CONFIGURATION ---
import pygame
import numpy as np

# Initialize the mixer
pygame.mixer.init(frequency=44100, size=-16, channels=1)

def create_tone(frequency, duration):
    """
    Generate a pygame Sound object for a sine wave of given frequency and duration.
    """
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    if frequency == 0:
        # Generate silence
        samples = np.zeros(num_samples, dtype=np.int16)
    else:
        t = np.linspace(0, duration, num_samples, False)
        wave = 0.5 * np.sin(2 * np.pi * frequency * t)
        # Convert to 16-bit signed integers
        samples = np.int16(wave * 32767)
    sound = pygame.sndarray.make_sound(samples)
    return sound

def start_sfx(sequence):
    """
    Play a sequence of (frequency, duration) tuples.
    """
    for freq, dur in sequence:
        sound = create_tone(freq, dur)
        sound.play()
        pygame.time.wait(int(dur * 1000))  # Wait until sound has played

# Now define your sound effect functions
def play_start_new_game():
    start_sfx([
        (523, 0.08),
        (659, 0.08),
        (784, 0.12),
        (0,   0.04),
        (784, 0.08),
        (988, 0.08),
        (1046, 0.16),
    ])

def play_shot_v1():
    start_sfx([
        (1400, 0.03),
        (900,  0.04),
    ])

def play_shot():
    start_sfx([
        (1500, 0.02),  # Higher pitch at the start
        (1300, 0.02),
        (1100, 0.02),
        (900, 0.04),   # Pitch drops
    ])

def play_hit():
    start_sfx([
        (1000, 0.06),
    ])

def play_wrong():
    start_sfx([
        (250, 0.12),
    ])

def play_level_up():
    start_sfx([
        (500, 0.04),
        (700, 0.04),
        (900, 0.04),
        (1200, 0.04),
    ])

def play_game_over():
    start_sfx([
        (600, 0.12),
        (450, 0.12),
        (320, 0.12),
        (220, 0.12),
    ])

def play_weapon_unlock():
    start_sfx([
        (800, 0.06),
        (1100, 0.06),
        (1500, 0.10),
    ])

def play_rocket():
    start_sfx([
        (400, 0.04),
        (600, 0.04),
        (900, 0.06),
        (1200, 0.08),
        (0,   0.04),
        (1200, 0.08),
        (0,   0.04),
        (1200, 0.08),
    ])

# --- WLED CONFIGURATION ---
WLED_IP = "10.20.0.118"  # Replace with your WLED device IP
WLED_URL = f"http://{WLED_IP}/json/state"

# Initialize Pygame
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("❌ No Xbox controller detected! Please plug one in.")
    sys.exit()

controller = pygame.joystick.Joystick(0)
controller.init()
print(f"🎮 Successfully connected to: {controller.get_name()}")

# Button mapping based on Xbox controller
BUTTON_Y = 3
BUTTON_X = 2
BUTTON_A = 0
BUTTON_B = 1
BUTTON_START = 7

# Mapping button indices to descriptive names for debug
BUTTON_MAP = {
    0: "A Button",
    1: "B Button",
    2: "X Button",
    3: "Y Button",
    4: "Left Bumper",
    5: "Right Bumper",
    6: "Back",
    7: "Start",
    8: "Left Stick",
    9: "Right Stick"
}

# Map buttons to colors
COLOR_MAP = {
    BUTTON_X: [0, 0, 255],        # Blue
    BUTTON_Y: [255, 255, 0],      # Yellow
    BUTTON_B: [255, 0, 0],        # Red
    BUTTON_A: [0, 255, 0],        # Green
}

# Limit rate for sending data (in seconds)
#SEND_INTERVAL = 0.1  # 100ms # WIFI OK
#SEND_INTERVAL = 0.05  # 50ms  # WIFI 1/100 times a error
SEND_INTERVAL = 0.06  # 60ms  # WIFI 1/100 times a error

async def send_leds(led_data):
    payload = {
        "on": True,
        "bri": 95,
        "seg": {"id": 0, "i": led_data}
    }
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.post(WLED_URL, json=payload, timeout=0.2)
            resp_text = await response.text()
            if response.status != 200:
                print(f"WARNING: WLED responded with status {response.status}: {resp_text}")
                print(f"DEBUG: Sending payload to WLED: {payload}")
            # Uncomment below for debugging responses
            else:
                print(f"DEBUG: WLED response: {resp_text}")
    except Exception as e:
        print(f"ERROR: Failed to send LED data: {e}")
        print(f"DEBUG: Sending payload to WLED: {payload}")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the event loop in a separate thread
    def run_loop():
        print("INFO: Starting asyncio event loop.")
        loop.run_forever()

    threading.Thread(target=run_loop, daemon=True).start()

    led_bullets = []
    last_send_time = 0  # timestamp of last send

    print("🚀 Starting main loop! Press Y/X/A/B to fire, Start to start game...")

    game_active = False
    running = True

    while running:
        try:
            events = pygame.event.get()
        except Exception as e:
            print(f"ERROR: pygame.event.get() failed: {e}")
            break

        current_time = time.time()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                btn = event.button
                btn_name = BUTTON_MAP.get(btn, f"Button {btn}")
                print(f"DEBUG: {btn_name} (button {btn}) pressed.")

                if btn == BUTTON_START:
                    print("🟢 Start button pressed! Starting game...")
                    game_active = True
                elif btn in COLOR_MAP:
                    color = COLOR_MAP[btn]
                    print(f"Firing color {color} for button {btn_name}")
                    play_shot()
                    led_bullets.append({'pos': 0, 'color': color})

        # Only send updates if rate limit allows
        if (current_time - last_send_time) >= SEND_INTERVAL:
            # Move bullets upward
            for bullet in led_bullets:
                bullet['pos'] += 1
            # Remove bullets off the top
            led_bullets = [b for b in led_bullets if b['pos'] < 250]

            # Create LED array
            led_array = [[0, 0, 0] for _ in range(250)]
            for b in led_bullets:
                if 0 <= b['pos'] < 250:
                    led_array[b['pos']] = b['color']

            # Send updated LED array
            asyncio.run_coroutine_threadsafe(send_leds(led_array), loop)
            last_send_time = current_time

        time.sleep(0.05)

    # Cleanup
    loop.call_soon_threadsafe(loop.stop)
    pygame.mixer.quit()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
