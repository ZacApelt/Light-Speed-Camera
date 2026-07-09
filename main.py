from machine import Pin
import time
import sys
import uselect

STEPS_PER_DEG = 30
MAX_SPEED_US = 800

LEFT_LIMIT_DEG = 45
RIGHT_LIMIT_DEG = -45
UPPER_LIMIT_DEG = 32
LOWER_LIMIT_DEG = -32

current_position_deg = (0, 0)

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
    global current_position_deg
    dir_x.value(not direction_x)
    dir_y.value(direction_y)
    for _ in range(steps_x):
        if (x_lim.value() == 0 and direction_x == 1) or (current_position_deg[0] >= LEFT_LIMIT_DEG and direction_x == 0):  # Check if the limit switch is triggered
            print("X-axis limit reached")
            current_position_deg = (RIGHT_LIMIT_DEG, current_position_deg[1])  # Update position to right limit
            break
        step_x.value(1)
        time.sleep_us(MAX_SPEED_US)
        step_x.value(0)
        time.sleep_us(MAX_SPEED_US)

    for _ in range(steps_y):
        if (y_lim.value() == 0 and direction_y == 1) or (current_position_deg[1] >= UPPER_LIMIT_DEG and direction_y == 0):  # Check if the limit switch is triggered
            print("Y-axis limit reached")
            current_position_deg = (current_position_deg[0], LOWER_LIMIT_DEG)  # Update position to lower limit
            break
        step_y.value(1)
        time.sleep_us(MAX_SPEED_US)
        step_y.value(0)
        time.sleep_us(MAX_SPEED_US)

def move_to_position(target_x_deg, target_y_deg):
    global current_position_deg
    current_x_deg, current_y_deg = current_position_deg

    # check if the target position is within the limits
    if target_x_deg > LEFT_LIMIT_DEG or target_x_deg < RIGHT_LIMIT_DEG:
        print(f"Target X position {target_x_deg} deg is out of bounds.")
        return
    if target_y_deg < LOWER_LIMIT_DEG or target_y_deg > UPPER_LIMIT_DEG:
        print(f"Target Y position {target_y_deg} deg is out of bounds.")
        return

    # Calculate the difference in position
    delta_x_deg = target_x_deg - current_x_deg
    delta_y_deg = target_y_deg - current_y_deg

    # Determine the direction for each axis
    direction_x = 0 if delta_x_deg > 0 else 1  # 0 for right, 1 for left
    direction_y = 0 if delta_y_deg > 0 else 1  # 0 for down, 1 for up

    # Calculate the number of steps needed for each axis
    steps_x = abs(int(delta_x_deg * STEPS_PER_DEG))
    steps_y = abs(int(delta_y_deg * STEPS_PER_DEG))

    # Move the motors
    move_xy(steps_x, steps_y, direction_x, direction_y)

    # Update the current position
    current_position_deg = (target_x_deg, target_y_deg)

def home():
    global current_position_deg

    dir_x.value(0)  # Move left
    dir_y.value(1)  # Move down

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

    current_position_deg = (RIGHT_LIMIT_DEG, LOWER_LIMIT_DEG)  # Reset position after homing

def trigger_scope():
    time.sleep(0.05)
    trigger.value(1)
    time.sleep(0.001)
    trigger.value(0)

home()
while True:
   print("current_position_deg:", current_position_deg)
   
   #move_to_position(0, new_y)
   new_x = float(input("Enter new x position (deg): "))
   new_y = float(input("Enter new y position (deg): "))
   move_to_position(new_x, new_y)

#move_to_position(-20, 20)

while True:
    time.sleep(0.1)


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
                    print("current_position_deg:", current_position_deg)
                elif "move" in line:
                    parts = line.split(":")[1].split(",")
                    target_x_deg = float(parts[0])
                    target_y_deg = float(parts[1])
                    move_to_position(target_x_deg, target_y_deg)
                    print("current_position_deg:", current_position_deg)
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