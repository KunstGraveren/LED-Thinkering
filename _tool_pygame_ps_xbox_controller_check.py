import pygame
import sys

# Initialize Pygame and the joystick subsystem
pygame.init()
pygame.joystick.init()

# Check for connected joysticks
if pygame.joystick.get_count() == 0:
    print("❌ No controller detected! Please plug in a controller.")
    sys.exit()

# Initialize the first controller
controller = pygame.joystick.Joystick(0)
controller.init()
name = controller.get_name()
print(f"🎮 Successfully connected to: {name}")

# Define mappings for Xbox Controller
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

XBOX_AXIS_MAP = {
    0: "Left Stick X (Horizontal)",
    1: "Left Stick Y (Vertical)",
    2: "Left Trigger (LT)",
    3: "Right Stick X (Horizontal)",
    4: "Right Stick Y (Vertical)",
    5: "Right Trigger (RT)"
}

# Define mappings for PS4 DualShock Controller
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

PS4_AXIS_MAP = {
    0: "Left Joystick X",
    1: "Left Joystick Y",
    2: "Right Joystick X",
    3: "Right Joystick Y",
    4: "Left Trigger",
    5: "Right Trigger"
}

# Detect controller type
controller_name_lower = name.lower()

if "dualshock" in controller_name_lower or "ps4 controller" in controller_name_lower:
    BUTTON_MAP = PS4_BUTTON_MAP
    AXIS_MAP = PS4_AXIS_MAP
    print("🕹️ Detected PS4 DualShock Controller")
else:
    # Xbox 360 Controller
    BUTTON_MAP = XBOX_BUTTON_MAP
    AXIS_MAP = XBOX_AXIS_MAP
    print("🕹️ Detected Xbox Controller")

# Main loop deadzone
DEADZONE = 0.15

print("\n🚀 Testing started! Press any button or move sticks to test...")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.JOYBUTTONDOWN:
            button_name = BUTTON_MAP.get(event.button, f"Unknown Button ({event.button})")
            print(f"🟢 [PRESSED]  -> {button_name} (Index {event.button})")
        elif event.type == pygame.JOYBUTTONUP:
            button_name = BUTTON_MAP.get(event.button, f"Unknown Button ({event.button})")
            print(f"🔴 [RELEASED] -> {button_name} (Index {event.button})")
        elif event.type == pygame.JOYHATMOTION:
            x, y = event.value
            direction = "Centered"
            if x == 1: direction = "Right"
            elif x == -1: direction = "Left"
            elif y == 1: direction = "Up"
            elif y == -1: direction = "Down"
            if x == 1 and y == 1:
                direction = "Up-Right"
            elif x == -1 and y == 1:
                direction = "Up-Left"
            elif x == 1 and y == -1:
                direction = "Down-Right"
            elif x == -1 and y == -1:
                direction = "Down-Left"
            print(f"🧭 [D-PAD]    -> Direction: {direction} (Value: {event.value})")
        elif event.type == pygame.JOYAXISMOTION:
            axis_name = AXIS_MAP.get(event.axis, f"Unknown Axis ({event.axis})")
            value = event.value
            if abs(value) > DEADZONE:
                print(f"🕹️ [AXIS]     -> {axis_name} moved to: {value:.2f}")

pygame.quit()
sys.exit()
