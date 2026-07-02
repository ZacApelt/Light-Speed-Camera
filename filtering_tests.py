import numpy as np
from scipy.signal import butter, filtfilt, convolve
import matplotlib.pyplot as plt


# time stamp in 0.1ns

# time vector
dt_ns = 0.5
t = np.arange(-15, 15, dt_ns)  # time vector from 0 to 100 ns with 0.1 ns step

# laser optical pulse
pulse_width = 3 # pulse duration in ns

laser_signal = np.zeros_like(t)

def laser_FWHM(t):
    return np.exp(-4 * np.log(2) * (t - pulse_width / 2) ** 2 / pulse_width ** 2)

# distort the laser pulse by skewing it to the right
def skewed_laser(t):
    skewness = 0  # positive skewness
    return laser_FWHM(t) * (1 + skewness * (t - pulse_width / 2) / pulse_width)

def squared_laser(t):
    return np.where((t >= 0) & (t <= pulse_width), 1, 0)

laser_signal = laser_FWHM(t)
#laser_signal = skewed_laser(t)
#laser_signal = squared_laser(t)


# PMT response (assymetric filter)
pmt_response = np.zeros_like(t)
t_rise = 1.4  # rise time in ns
t_fall = 3.0  # fall time in ns
pmt_bandwidth = 0.35 / t_rise * 1e9  # bandwidth in Hz
print(f"PMT bandwidth: {pmt_bandwidth:.2e} Hz")
# pmt is a lpf with a cutoff frequency corresponding to the bandwidth
def pmt_filter(t):
    t = t * 1e-9  # convert ns to seconds
    tau = 1 / (2 * np.pi * pmt_bandwidth)  # time constant

    return np.exp(-t / tau) * (t >= 0) + (t + t_rise / 1e9) / (t_rise / 1e9) * (t < 0) * (t >= -t_rise * 1e-9)
    # linear rise and linear decay
    #return (t + t_rise / 1e9) / (t_rise / 1e9) * (t < 0) * (t >= -t_rise * 1e-9) + (t>=0) * (t <= t_fall * 1e-9) * (1 - t / (t_fall * 1e-9))

pmt_response = pmt_filter(t)

# oscilloscope response
scope_bandwidth = 70_000_000  # bandwidth in Hz
def scope_filter(t):
    t = t * 1e-9  # convert ns to seconds
    tau = 1 / (2 * np.pi * scope_bandwidth)  # time constant
    print(f"Scope time constant: {tau:.2e} s")
    return np.exp(-t / tau) * (t >= 0) / (tau * 1e9)  # normalize to have unit area

scope_response = scope_filter(t)

# convolve the laser signal with the PMT response and the scope response
pmt_output = convolve(laser_signal, pmt_response, mode='same') * dt_ns  # scale by the time step
scope_output = convolve(pmt_output, scope_response, mode='same') * dt_ns  # scale by the time step
system_response = convolve(pmt_response, scope_response, mode='same') * dt_ns

# attempt to deconvolve the scope response from the scope output to recover the laser signal using Wiener deconvolution
def wiener_deconvolution(signal, kernel, noise_power, sample_spacing):
    signal_centered = np.fft.ifftshift(signal)
    kernel_centered = np.fft.ifftshift(kernel)

    signal_fft = np.fft.fft(signal_centered)
    kernel_fft = np.fft.fft(kernel_centered, n=len(signal)) * sample_spacing
    kernel_power = np.abs(kernel_fft) ** 2
    wiener_filter = np.conj(kernel_fft) / (kernel_power + noise_power)
    deconvolved_fft = signal_fft * wiener_filter
    deconvolved_signal = np.fft.ifft(deconvolved_fft)
    return np.fft.fftshift(np.real(deconvolved_signal))
noise_power = 0.01  # assume some noise power
deconvolved_signal = wiener_deconvolution(scope_output, system_response, noise_power, dt_ns)

# plot the laser pulse
plt.figure(figsize=(12, 10))
plt.subplot(4, 1, 1)
# plot laser power and scope_output on the same plot
plt.plot(t, laser_signal, label='Laser Pulse')
plt.title('Laser Optical Pulse')
plt.ylabel('Amplitude')
plt.grid()

plt.subplot(4, 1, 2)
plt.plot(t, pmt_response, label='PMT Response', color='orange')
plt.title('PMT Response (Asymmetric Filter)')
plt.ylabel('Amplitude')
plt.grid()

plt.subplot(4, 1, 3)
plt.plot(t, scope_response, label='Scope Response', color='green')
plt.title('Oscilloscope Response (Low-Pass Filter)')
plt.ylabel('Amplitude')
plt.grid()

plt.subplot(4, 1, 4)
plt.plot(t, deconvolved_signal, label='Deconvolved Signal', color='purple')
plt.plot(t, laser_signal, label='Laser Pulse')
plt.plot(t, scope_output, label='Scope Output', color='red', linestyle='--')
plt.title('Deconvolved Signal')
plt.ylabel('Amplitude')
plt.grid()

plt.show()

