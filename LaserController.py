import serial
import time



class Laser:
    def __init__(self, port="COM5"):
        self.ser = serial.Serial(
            port,
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
        if not self.ser.is_open:
            print(f"Failed to open serial port {port}")
        
        self.las_on = False
        self.las_working = False
        self.shutter_open = False
        self.las_ready = False
        self.las_mode = None

        self.burst_quantity = 0
        self.frequency = 0
        self.hv = 0
        self.last_energy = 0
        self.energies = []
        self.supply_voltage = 0
        self.temp1 = 0
        self.temp2 = 0
        self.quantity_counter = 0
        self.total_shot_counter = 0
        self.transmission_percentage = 0

        self.EE_error = False
        self.pem_error = False
        self.temp_warning = False
        self.temp_limit = False
        self.static_error = False
        self.op_error = False
        
    def fcs(self, s):
        return f"{sum(s.encode('ASCII')) % 256:02X}"

    def cmd(self, body):
        msg = "#!@" + body
        return (msg + self.fcs(msg) + "\r").encode("ASCII")

    def send(self, body, delay=0.1):  
        packet = self.cmd(body)
        #input("Press Enter to send: " + packet.decode("ASCII").strip())
        #print("Sending:", packet.decode("ASCII").strip())
        self.ser.write(packet)
        self.ser.flush()
        time.sleep(delay)
        reply = self.ser.read_all()
        #print("Reply:", reply)
        return reply.decode("ASCII").strip()

    def laser_on(self):
        self.send("g")       # LaserOn / standby
    
    def laser_off(self):
        self.send("i")       # LaserOff / standby

    def set_hv(self, percent):
        # percent should be between 0 and 100
        hv_hex = hex(percent)[2:].upper()
        self.send("n" + hv_hex)     # Set HV to percent%

    def set_freq(self, hz):
        # hz should be between 1 and 20
        self.send("m" + f"{hz:02d}")     # Set repetition rate to hz Hz

    def open_shutter(self):
        self.send("z1")      # Open shutter

    def close_shutter(self):
        self.send("z0")      # Close shutter

    def set_rep_on(self):
        self.send("h")       # Repetition on
    
    def set_external_trig_mode(self):
        self.send("u")       # Set external trigger mode
    
    def set_burst_mode(self):
        self.send("j")       # Set burst mode
    
    def set_burst_quantity(self, quantity):
        # quantity is represented with 4 hex digits, so max is 65535
        quantity_hex = f"{quantity:04X}"
        self.send("l" + quantity_hex)
    
    def set_transmission_percentage(self, percent):
        # percent should be between 0 and 100 in steps of 0.5
        percent_hex = hex(int(percent * 2))[2:].upper()
        self.send("O4" + percent_hex)     # Set transmission percentage to percent%
    
    def set_stepper_position(self, position):
        # position is represented with 4 decimal digits, so max is 399
        position_hex = f"{position:04d}"
        self.send("O3" + position_hex)     # Set stepper position to position
    
    def init_attenuator(self):
        self.send("O60000")       # Initialize attenuator
    
    def get_short_status(self):
        status = self.send("W")
        try:
            status_flag_byte = status[4:6]
            las_on = bool(int(status_flag_byte, 16) & 0b00000001)
            las_working = bool(int(status_flag_byte, 16) & 0b00000010)
            EE_error = bool(int(status_flag_byte, 16) & 0b00001000)
            pem_error = bool(int(status_flag_byte, 16) & 0b00010000)
            temp_warning = bool(int(status_flag_byte, 16) & 0b00100000)
            static_error = bool(int(status_flag_byte, 16) & 0b01000000)
            op_error = bool(int(status_flag_byte, 16) & 0b10000000)
            #print("Short status:", status)
            if EE_error or pem_error or temp_warning or static_error or op_error:
                print("Errors detected:")
                if EE_error:
                    print(" - EE Error")
                if pem_error:
                    print(" - Pem Error")
                if temp_warning:
                    print(" - Temperature Warning")
                if static_error:
                    print(" - Static Error")
                if op_error:
                    print(" - Operation Error")
            elif las_on and las_working:
                #print("Laser is on and working")
                pass
        except Exception as e:
            print("Failed to parse short status:", e)

    def get_full_status(self):
        status1 = self.send("UT")
        status2 = self.send("UU")
        #print("Full status:", status1, status2)

        aa = status1[5:7]
        oo = status1[9:11]
        eeee = status1[11:15]
        ff = status1[15:17]
        ii = status1[17:19]
        zzzz = status1[23:27]

        pp = status2[5:7]
        qq = status2[7:9]
        gg = status2[9:11]
        hh = status2[11:13]
        nn = status2[13:15]
        kkkk = status2[15:19]
        xxxx = status2[21:23]
        yyyyyyyy = status2[23:31]

        shutter_open = bool(int(aa, 16) & 0b00000001)
        las_ready = bool(int(aa, 16) & 0b00000100)
        las_on = bool(int(aa, 16) & 0b00001000)
        # get first 4 bits of aa for repetition mode
        first_4_bits_aa = (int(aa, 16) & 0b11110000) >> 4
        if first_4_bits_aa == 0b0000:
            las_mode = "off"
        elif first_4_bits_aa == 0b0001:
            las_mode = "repetition"
        elif first_4_bits_aa == 0b0010:
            las_mode = "burst"
        elif first_4_bits_aa == 0b0100:
            las_mode = "external trigger"
        
        self.burst_quantity = int(eeee, 16)
        self.frequency = int(ff, 16)
        self.hv = int(ii, 16)
        self.last_energy = int(zzzz, 16) / 64000 * 250

        self.static_error = bool(int(pp, 16) & 0b00000001)
        self.temp_limit = bool(int(pp, 16) & 0b00001000)
        self.temp_warning = bool(int(pp, 16) & 0b00010000) or bool(int(pp, 16) & 0b00100000)
        self.pem_error = bool(int(pp, 16) & 0b01000000)
        self.op_error = bool(int(qq, 16) & 0b00000001)
        self.supply_voltage = int(gg, 16) * 0.11
        self.temp1 = int(hh, 16)
        self.temp2 = int(nn, 16)
        self.last_energy = int(kkkk, 16) / 64000 * 250
        self.quantity_counter = int(xxxx, 16)
        self.total_shot_counter = int(yyyyyyyy, 16)
        
    def get_version_info(self):
        version = self.send("V3")
        #print("Version info:", version)
        vv = version[6:8]
        if vv == "73":
            #print("No shutter, attenuation supported, no HV control, can measure energy")
            pass
    
    def get_attenuator_status(self):
        status = self.send("UV")
        #print("Attenuator status:", status)
        dd = status[15:17]
        self.transmission_percentage = int(dd, 16) / 2
    
    def get_energy_values(self):
        energy = self.send("P")
        #print("Energy values:", energy)
        self.energies = []
        aa = energy[4:6]
        if len(aa) < 2:
            return
        number_of_values = int(aa, 16)
        for i in range(number_of_values):
            energy_hex = energy[8 + i*4 : 12 + i*4]
            #print(energy_hex)
            if len(energy_hex) < 4:
                break
            energy_value = int(energy_hex, 16) / 64000 * 250
            self.energies.append(energy_value)
    
    def display_useful_status(self):
        laser.get_short_status()
        laser.get_full_status()
        laser.get_version_info()
        laser.get_attenuator_status()
        laser.get_energy_values()

        #print(f"\nLASER MODE: Laser on: {self.las_on}, Laser working: {self.las_working}, Laser ready: {self.las_ready}, Laser mode: {self.las_mode}")
        print(f"PARAMETERS: Burst quantity: {self.burst_quantity}, Frequency: {self.frequency} Hz, HV: {self.hv}%, Transmission percentage: {self.transmission_percentage}%")
        print(f"METRICS: Last energy: {self.last_energy} uJ, Supply voltage: {self.supply_voltage} V, Temp1: {self.temp1} C, Temp2: {self.temp2} C, Total shot counter: {self.total_shot_counter}\n\n")

laser = Laser("COM26")

# turn on laser
laser.laser_on()
time.sleep(10)
laser.set_hv(100)
laser.set_freq(5)
laser.set_transmission_percentage(100)
laser.open_shutter()
laser.set_rep_on()


try:
    while True:
        laser.display_useful_status()
        time.sleep(2)

except KeyboardInterrupt:
    print("Turning off laser...")
    laser.laser_off()
