import pygame
import sys

# Initialize Pygame and the joystick subsystem
pygame.init()
pygame.joystick.init()

# Check for connected joysticks
if pygame.joystick.get_count() == 0:
    print("❌ No Xbox controller detected! Please plug one in.")
    sys.exit()

# Initialize the first controller
controller = pygame.joystick.Joystick(0)
controller.init()
print(f"🎮 Successfully connected to: {controller.get_name()}")

# Standard Xbox Controller Button Mapping (Windows/Linux standard)
BUTTON_MAP = {
    0: "A Button",
    1: "B Button",
    2: "X Button",
    3: "Y Button",
    4: "Left Bumper (LB)",
    5: "Right Bumper (RB)",
    6: "Back / View Button",
    7: "Start / Menu Button",
    8: "Left Stick Click (LSB)",
    9: "Right Stick Click (RSB)",
    10: "Xbox Guide Button"
}

AXIS_MAP = {
    0: "Left Stick X (Horizontal)",
    1: "Left Stick Y (Vertical)",
    2: "Left Trigger (LT)",
    3: "Right Stick X (Horizontal)",
    4: "Right Stick Y (Vertical)",
    5: "Right Trigger (RT)"
}

# Main loop deadzone to filter minor stick drift
DEADZONE = 0.15

print("\n🚀 Testing started! Press any button or move sticks to test...")
running = True

while running:
    # Pygame requires pumping the event queue to update controller states
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 1. TEST: Digital Buttons (Press)
        elif event.type == pygame.JOYBUTTONDOWN:
            button_name = BUTTON_MAP.get(event.button, f"Unknown Button ({event.button})")
            print(f"🟢 [PRESSED]  -> {button_name} (Index {event.button})")

        # 2. TEST: Digital Buttons (Release)
        elif event.type == pygame.JOYBUTTONUP:
            button_name = BUTTON_MAP.get(event.button, f"Unknown Button ({event.button})")
            print(f"🔴 [RELEASED] -> {button_name} (Index {event.button})")

        # 3. TEST: D-Pad / Hat Motion
        elif event.type == pygame.JOYHATMOTION:
            # event.value returns a tuple like (x, y) containing -1, 0, or 1
            x, y = event.value
            direction = "Centered"
            if x == 1: direction = "Right"
            elif x == -1: direction = "Left"
            elif y == 1: direction = "Up"
            elif y == -1: direction = "Down"

            # Catch diagonal combinations
            if x == 1 and y == 1: direction = "Up-Right"
            elif x == -1 and y == 1: direction = "Up-Left"
            elif x == 1 and y == -1: direction = "Down-Right"
            elif x == -1 and y == -1: direction = "Down-Left"

            print(f"🧭 [D-PAD]    -> Direction: {direction} (Value: {event.value})")

        # 4. TEST: Analog Sticks and Triggers
        elif event.type == pygame.JOYAXISMOTION:
            axis_name = AXIS_MAP.get(event.axis, f"Unknown Axis ({event.axis})")
            value = event.value

            # Apply deadzone filtering so console isn't flooded by minor drift
            if abs(value) > DEADZONE:
                # Triggers on some OS sit at -1.0 when idle, map accordingly if needed
                print(f"🕹️ [AXIS]     -> {axis_name} moved to: {value:.2f}")

# Clean exit
pygame.quit()
sys.exit()
