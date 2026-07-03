from machine import Pin
import time
import sys
import uselect

STEPS_PER_MM = 160
MAX_SPEED_US = 800

LEFT_LIMIT_MM = -49
RIGHT_LIMIT_MM = 55
UPPER_LIMIT_MM = 60
LOWER_LIMIT_MM = -45

current_position_mm = (0, 0)

step_x_pin = 16
dir_x_pin = 17

step_y_pin = 20
dir_y_pin = 21

trigger_pin = 15

x_lim_pin = 9
y_lim_pin = 6

step_x = Pin(step_x_pin, Pin.OUT)
dir_x = Pin(dir_x_pin, Pin.OUT)
step_y = Pin(step_y_pin, Pin.OUT)
dir_y = Pin(dir_y_pin, Pin.OUT)
trigger = Pin(trigger_pin, Pin.OUT)
x_lim = Pin(x_lim_pin, Pin.IN, Pin.PULL_UP)
y_lim = Pin(y_lim_pin, Pin.IN, Pin.PULL_UP)

'''
x: direction 1 = left, 0 = right
y: direction 1 = up, 0 = down

'''

def move_xy(steps_x, steps_y, direction_x, direction_y):
    global current_position_mm
    dir_x.value(not direction_x)
    dir_y.value(direction_y)
    for _ in range(steps_x):
        if (x_lim.value() == 0 and direction_x == 0) or (current_position_mm[0] <= LEFT_LIMIT_MM and direction_x == 1):  # Check if the limit switch is triggered
            print("X-axis limit reached")
            current_position_mm = (RIGHT_LIMIT_MM, current_position_mm[1])  # Update position to right limit
            break
        step_x.value(1)
        time.sleep_us(MAX_SPEED_US)
        step_x.value(0)
        time.sleep_us(MAX_SPEED_US)

    for _ in range(steps_y):
        if (y_lim.value() == 0 and direction_y == 0) or (current_position_mm[1] >= UPPER_LIMIT_MM and direction_y == 1):  # Check if the limit switch is triggered
            print("Y-axis limit reached")
            current_position_mm = (current_position_mm[0], LOWER_LIMIT_MM)  # Update position to lower limit
            break
        step_y.value(1)
        time.sleep_us(MAX_SPEED_US)
        step_y.value(0)
        time.sleep_us(MAX_SPEED_US)

def move_to_position(target_x_mm, target_y_mm):
    global current_position_mm
    current_x_mm, current_y_mm = current_position_mm

    # check if the target position is within the limits
    if target_x_mm < LEFT_LIMIT_MM or target_x_mm > RIGHT_LIMIT_MM:
        print(f"Target X position {target_x_mm} mm is out of bounds.")
        return
    if target_y_mm < LOWER_LIMIT_MM or target_y_mm > UPPER_LIMIT_MM:
        print(f"Target Y position {target_y_mm} mm is out of bounds.")
        return

    # Calculate the difference in position
    delta_x_mm = target_x_mm - current_x_mm
    delta_y_mm = target_y_mm - current_y_mm

    # Determine the direction for each axis
    direction_x = 0 if delta_x_mm > 0 else 1  # 0 for right, 1 for left
    direction_y = 1 if delta_y_mm > 0 else 0  # 1 for up, 0 for down

    # Calculate the number of steps needed for each axis
    steps_x = abs(int(delta_x_mm * STEPS_PER_MM))
    steps_y = abs(int(delta_y_mm * STEPS_PER_MM))

    # Move the motors
    move_xy(steps_x, steps_y, direction_x, direction_y)

    # Update the current position
    current_position_mm = (target_x_mm, target_y_mm)

def home():
    global current_position_mm

    dir_x.value(1)  # Move left
    dir_y.value(0)  # Move down

    while x_lim.value() == 1:
        step_x.value(1)
        time.sleep_us(MAX_SPEED_US)
        step_x.value(0)
        time.sleep_us(MAX_SPEED_US)
    while y_lim.value() == 1:
        step_y.value(1)
        time.sleep_us(MAX_SPEED_US)
        step_y.value(0)
        time.sleep_us(MAX_SPEED_US)

    current_position_mm = (RIGHT_LIMIT_MM, LOWER_LIMIT_MM)  # Reset position after homing

def trigger_scope():
    trigger.value(1)
    time.sleep_us(100)
    trigger.value(0)

#home()
#while True:
#    new_y = int(input("Enter new y position (mm): "))
#    move_to_position(50, new_y)

#while True:
#    time.sleep(0.1)


spoll = uselect.poll()
spoll.register(sys.stdin, uselect.POLLIN)

updateFlag = False
last_received_time = time.time()

while True:
    time.sleep(0.01)
    
    if spoll.poll(0):  # Poll with a timeout of 0 (non-blocking check)
        data = sys.stdin.read(1)  # Read one byte if data is available
        if data:
            try:
                line = (data + sys.stdin.readline()).strip()  # Read the rest of the line

                if "stop" in line:
                    pass
                elif "home" in line:
                    home()
                    print("current_position_mm:", current_position_mm)
                elif "move" in line:
                    parts = line.split(":")[1].split(",")
                    target_x_mm = float(parts[0])
                    target_y_mm = float(parts[1])
                    move_to_position(target_x_mm, target_y_mm)
                    print("current_position_mm:", current_position_mm)
                elif "ping" in line:
                    print("pong")
                elif "trigger" in line:
                    trigger_scope()
                    print("Scope triggered")
                else:
                    print(f"command \"{line}\" not recognized")

                updateFlag = True
                last_received_time = time.time()

                print("ok")

            except (ValueError, IndexError):
                print(f"command \"{line}\" caused an error")
    
    # do stuff here