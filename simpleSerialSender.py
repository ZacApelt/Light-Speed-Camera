import serial
import time

ser = serial.Serial('COM4', 115200, timeout=1) 


def wait_for_response(timeout=30):
    start_time = time.time()

    while time.time() - start_time < timeout:
        line = ser.readline().decode(errors="ignore").strip()

        if not line:
            continue

        print("Pico:", line)

        if line == "ok":
            return True

    print("Timeout waiting for response")
    return False


def send_command(command, timeout=60):
    print("Sending:", command)

    # Clear stale responses before sending new command
    ser.reset_input_buffer()

    ser.write((command + "\n").encode())
    ser.flush()

    ok = wait_for_response(timeout=timeout)
    if not ok:
        raise TimeoutError(f"No ok from Pico after command: {command}")
    

send_command("home")
send_command("move:8,8")

input("Press Enter to start:")
for i in range(64):
    send_command("trigger")
    send_command(f"move:0,{8 - i * 0.25}")
    time.sleep(1)
    send_command("trigger")
    send_command(f"move:-8,{8 - i * 0.25}")
    time.sleep(1)
    send_command(f"move:8,{8 - (i+1) * 0.25}")
    print(f"done {i+1}/64")
