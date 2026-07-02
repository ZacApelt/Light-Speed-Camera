import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter, freqz
from scipy.fft import fft, ifft
import math
import time

signal =  [201, 201, 201, 201, 201, 201, 201, 201, 201, 201, 201, 201, 201, 201, 202, 202, 202, 202, 201, 201, 201, 201, 201, 201, 202, 201, 201, 200, 196, 186, 166, 136, 103, 72, 49, 35, 32, 34, 35, 38, 41, 46, 53, 59, 66, 73, 79, 84, 88, 92, 96, 99, 102, 105, 108, 111, 114, 116, 119, 120, 122, 122, 122, 122, 123, 123, 124, 125, 126, 126, 127, 126, 126, 125, 124, 123, 121, 121, 121, 121, 122, 122, 123, 123, 122, 122, 122, 121, 121, 120, 119, 118, 118, 117, 117, 117, 117, 117, 117, 118, 119, 121, 124, 127, 131, 135, 140, 143, 146, 149, 152, 154, 155, 157, 158, 159, 160, 161, 162, 163, 164, 164, 165, 166, 166, 167, 168, 168, 169, 170, 170, 170, 170, 170, 170, 170, 171, 171, 171, 171, 171, 171, 171, 171, 171, 171, 171, 171, 171, 171, 170, 170, 170, 170, 170, 170, 170, 171, 171, 172, 173, 173, 174, 174, 174, 175, 175, 175, 175, 174, 174, 174, 174, 175, 176, 176, 176, 177, 177, 178, 178, 179, 179, 179, 179, 179, 180, 180, 180, 181, 180, 180, 180, 180, 180, 180, 181, 181, 181, 182]

signal = np.array(signal)  # Convert to numpy array for easier manipulation

t = np.linspace(0, 200e-9, len(signal))  # Time vector from 0 to 200 ns

# flip the signal
signal = -signal

# normalise
signal = signal / np.max(np.abs(signal)) + 1

fast_num = [-0.01189, 0.0275, -0.02653, 0.02003, 0.01363, 0.02838, 0.01931, 0.001311, 0.01355, 0.01309, -0.002543 ]
fast_den = [1, -3.302, 4.706, -3.741, 1.69, -0.3426]
slow_num = [-0.01189, 0.0271, -0.021, 0.01146, 0.01704]
slow_den = [1, -3.269, 4.209, -2.554, 0.6227]


def nextpow2(x):
    """
    Returns the exponent of the smallest power of 2 that is 
    greater than or equal to the absolute value of x.
    """
    # Handle absolute value as per MATLAB specification
    x = abs(x)
    
    if x == 0:
        return 0
        
    # If x is a float, round it up to the next integer 
    if isinstance(x, float):
        x = math.ceil(x)
        
    # (x - 1).bit_length() perfectly finds the required power of 2 exponent
    return (x - 1).bit_length()


def inverse_filter_regularised(y, b, a, alpha=0.1):
    # implementation of weiner deconvolution with regularization
    # y: input signal
    # b: numerator coefficients of the filter
    # a: denominator coefficients of the filter
    # alpha: regularization parameter

    # H(z) = B(z) / A(z)
    # X = Y * conj(H) / (abs(H)^2 + alpha)

    y = np.asarray(y, dtype=float).ravel()
    b = np.asarray(b, dtype=float)
    a = np.asarray(a, dtype=float)

    N = len(y)
    Nfft = 2 ** nextpow2(4 * N)

    # scipy returns w, H
    w, H = freqz(b, a, worN=Nfft, whole=True)

    Y = fft(y, Nfft)

    X = Y * np.conj(H) / (np.abs(H)**2 + alpha)

    x_full = np.real(ifft(X))
    return x_full[:N]

x_est_fast = inverse_filter_regularised(signal, fast_num, fast_den)
start_time = time.time()
x_est_slow = inverse_filter_regularised(signal, slow_num, slow_den)
print("Slow deconvolution took", time.time() - start_time, "seconds")
    


plt.plot(t, signal, label='Original Signal', color='green')
plt.plot(t, x_est_fast, label='Fast Deconvolution', color='orange')
plt.plot(t, x_est_slow, label='Slow Deconvolution', color='blue')
plt.xlabel("Time (s)")
plt.ylabel("Signal")
plt.title("Open Tube Across Beam Dump")
ax = plt.gca()
ax.set_xticks(np.arange(0, 200e-9 + 20e-9, 20e-9))
ax.set_xticklabels([f"{int(x*1e9)} ns" for x in np.arange(0, 200e-9 + 20e-9, 20e-9)])
plt.legend()
plt.show()
