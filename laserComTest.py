import serial
import time

def fcs(s):
    return f"{sum(s.encode('ASCII')) % 256:02X}"

def cmd(body):
    msg = "#!@" + body
    return (msg + fcs(msg) + "\r").encode("ASCII")

ser = serial.Serial(
    "COM5",
    baudrate=9600,
    bytesize=8,
    parity=serial.PARITY_NONE,
    stopbits=1,
    timeout=0.2,
    write_timeout=5,
    rtscts=False,
    dsrdtr=False,
    xonxoff=False,
)

def send(body, delay=0.2):  
    packet = cmd(body)
    #input("Press Enter to send: " + packet.decode("ASCII").strip())
    print("Sending:", packet.decode("ASCII").strip())
    ser.write(packet)
    ser.flush()
    time.sleep(delay)
    print("Reply:", ser.read_all())


send("g")       # LaserOn / standby
time.sleep(10)
send("n64")     # Set HV to 50%
send("m02")     # Set repetition rate to 2 Hz
send("z1")      # Open shutter
send("h")       # Repetition on