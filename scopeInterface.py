import time
from dataclasses import dataclass
import numpy as np
import pyvisa


@dataclass
class ScopeTrace:
    t: np.ndarray
    v: np.ndarray
    channel: int
    x_increment: float
    x_origin: float


class DSOX2004A:
    def __init__(self, resource: str | None = None, timeout_ms: int = 1000):
        self.rm = pyvisa.ResourceManager("@py")
        print(self.rm.list_resources())
        if resource is None:
            resources = self.rm.list_resources()
            if not resources:
                raise RuntimeError("No VISA instruments found.")
            resource = resources[0]

        self.inst = self.rm.open_resource(resource)
        self.inst.timeout = timeout_ms
        self.inst.chunk_size = 1024 * 1024
        self.inst.write_termination = "\n"
        self.inst.read_termination = "\n"

        print(self.query("*IDN?").strip())

    def write(self, cmd: str):
        self.inst.write(cmd)

    def query(self, cmd: str) -> str:
        return self.inst.query(cmd)

    def close(self):
        self.inst.close()
        self.rm.close()

    def reset(self):
        self.write("*CLS")
        self.write(":STOP")

    def set_channel(
        self,
        ch: int,
        scale: float,
        offset: float = 0.0,
        probe: float = 1.0,
        coupling: str = "DC",
        impedance: str = "ONEM",
        display: bool = True,
        invert: bool = False,
        bw_limit: bool = False,
    ):
        """
        scale: V/div
        offset: vertical offset in V
        probe: probe ratio, e.g. 1, 10
        impedance: "ONEM" or "FIFT"
        """
        self.write(f":CHANnel{ch}:DISPlay {'ON' if display else 'OFF'}")
        self.write(f":CHANnel{ch}:SCALe {scale}")
        self.write(f":CHANnel{ch}:OFFSet {offset}")
        self.write(f":CHANnel{ch}:PROBe {probe}")
        self.write(f":CHANnel{ch}:COUPling {coupling}")
        self.write(f":CHANnel{ch}:IMPedance {impedance}")
        self.write(f":CHANnel{ch}:INVert {'ON' if invert else 'OFF'}")
        self.write(f":CHANnel{ch}:BWLimit {'ON' if bw_limit else 'OFF'}")

    def set_timebase(
        self,
        scale: float,
        position: float = 0.0,
        reference: str = "CENTer",
    ):
        """
        scale: seconds/div
        position: trigger/time position in seconds
        """
        self.write(f":TIMebase:SCALe {scale}")
        self.write(f":TIMebase:POSition {position}")
        self.write(f":TIMebase:REFerence {reference}")

    def set_edge_trigger(
        self,
        source: str = "CHANnel2",
        level: float = 1.0,
        slope: str = "POSitive",
        coupling: str = "DC",
        sweep: str = "NORMal",
    ):
        """
        source examples: CHANnel1, CHANnel2, EXTernal
        slope: POSitive, NEGative, EITHer
        sweep: AUTO or NORMal
        """
        self.write(":TRIGger:MODE EDGE")
        self.write(f":TRIGger:EDGE:SOURce {source}")
        self.write(f":TRIGger:EDGE:LEVel {level}")
        self.write(f":TRIGger:EDGE:SLOPe {slope}")
        self.write(f":TRIGger:EDGE:COUPling {coupling}")
        self.write(f":TRIGger:SWEep {sweep}")

    def set_acquisition(self, points: int = 1000, acquire_type: str = "NORMal"):
        """
        Keep points low if you want 20 Hz transfers.
        """
        self.write(f":ACQuire:TYPE {acquire_type}")
        self.write(f":WAVeform:POINts {points}")
        self.write(":WAVeform:POINts:MODE RAW")
        self.write(":WAVeform:FORMat BYTE")
        self.write(":WAVeform:UNSigned ON")

    def arm_single(self):
        self.write(":SINGle")

    def wait_for_trigger(self, timeout_s: float = 1.0) -> bool:
        """
        Poll run state until acquisition stops.
        Requires newer firmware for :RSTate?.
        """
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < timeout_s:
            state = self.query(":RSTate?").strip().upper()
            if "STOP" in state:
                return True
            time.sleep(0.002)
        return False

    def digitize(self, channels=(1, 2), timeout_s: float = 1.0):
        """
        Blocking acquisition. Often safer than :SINGle + polling.
        """
        ch_list = ",".join(f"CHANnel{ch}" for ch in channels)
        old_timeout = self.inst.timeout
        self.inst.timeout = int(timeout_s * 1000)
        try:
            self.write(f":DIGitize {ch_list}")
            self.query("*OPC?")
        finally:
            self.inst.timeout = old_timeout

    def read_channel(self, ch: int) -> ScopeTrace:
        self.write(f":WAVeform:SOURce CHANnel{ch}")

        xinc = float(self.query(":WAVeform:XINCrement?"))
        xorig = float(self.query(":WAVeform:XORigin?"))
        yinc = float(self.query(":WAVeform:YINCrement?"))
        yorig = float(self.query(":WAVeform:YORigin?"))
        yref = float(self.query(":WAVeform:YREFerence?"))

        raw = self.inst.query_binary_values(
            ":WAVeform:DATA?",
            datatype="B",
            is_big_endian=False,
            container=np.array,
        )

        v = ((raw - yref) * yinc) + yorig
        t = xorig + np.arange(len(v)) * xinc

        return ScopeTrace(t=t, v=v, channel=ch, x_increment=xinc, x_origin=xorig)

    def read_channel_fast(self, ch: int) -> ScopeTrace:
        self.write(f":WAVeform:SOURce CHANnel{ch}")

        raw = self.inst.query_binary_values(
            ":WAVeform:DATA?",
            datatype="B",
            is_big_endian=False,
            container=np.array,
        )

        return ScopeTrace(t=np.array([]), v=raw, channel=ch, x_increment=0.0, x_origin=0.0)

    def capture_once(self, channels=(1, 2), timeout_s: float = 1.0):
        """
        Acquires one triggered record and returns traces.
        """
        self.digitize(channels=channels, timeout_s=timeout_s)
        #return {ch: self.read_channel(ch) for ch in channels}
        return {ch: self.read_channel_fast(ch) for ch in channels}

    def capture_loop(self, n: int, channels=(1, 2), timeout_s: float = 1.0):
        """
        Generator yielding repeated triggered captures.
        """
        for i in range(n):
            t0 = time.perf_counter()
            traces = self.capture_once(channels=channels, timeout_s=timeout_s)
            yield i, traces, time.perf_counter() - t0



scope = DSOX2004A("USB0::2391::6042::MY51350320::0::INSTR")  # or DSOX2004A("USB0::0x0957::...::INSTR")

scope.reset()

def setup_for_continuous_capture(scope: DSOX2004A):
    scope.set_channel(1, scale=0.01, offset=0, probe=1, impedance="ONEM")
    scope.set_channel(2, scale=0.5, offset=0, probe=1, impedance="ONEM")

    scope.set_timebase(scale=20e-9, position=0)
    scope.set_edge_trigger(source="CHANnel2", level=1, slope="POSitive", sweep="NORMal")
    scope.set_acquisition(points=500)

    for i, traces, dt in scope.capture_loop(100, channels=(1, 2), timeout_s=1.0):
        ch1 = traces[1]
        ch2 = traces[2]
        print(i, f"{dt*1000:.1f} ms", len(ch1.t))

    print(ch1, ch2)


def test_impulse_response(scope: DSOX2004A):
    scope.set_channel(1, scale=0.5, offset=-1.5, probe=1, impedance="ONEM")

    scope.set_timebase(scale=20e-9, position=70e-9)
    scope.set_edge_trigger(source="CHANnel1", level=-1.4, slope="NEGative", sweep="NORMal")
    scope.set_acquisition(points=200)


    for i, traces, dt in scope.capture_loop(1, channels=(1,), timeout_s=1.0):
        ch1 = traces[1]
        print(i, f"{dt*1000:.1f} ms", len(ch1.t))

    # print(measurements[0])
    # # average all the measurements together to get a cleaner impulse response
    # average_measurement = np.mean([m.v for m in measurements], axis=0)
    # print(average_measurement)
    print(ch1.v)

    for m in ch1.v:
        print(m)

#test_impulse_response(scope)


