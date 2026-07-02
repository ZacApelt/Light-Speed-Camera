import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter, freqz
from scipy.fft import fft, ifft
import math
import time

signal =  [211, 211, 211, 211, 211, 211, 211, 212, 212, 212, 212, 212, 211,
       211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 212, 212,
       212, 212, 212, 211, 211, 208, 200, 187, 169, 149, 130, 115, 104,
        97,  92,  87,  78,  68,  58,  48,  42,  39,  40,  42,  44,  47,
        51,  57,  62,  68,  75,  81,  86,  91,  96, 100, 104, 108, 111,
       114, 117, 120, 123, 126, 130, 134, 138, 141, 144, 147, 150, 152,
       154, 156, 158, 159, 159, 159, 158, 157, 156, 155, 154, 153, 152,
       153, 153, 153, 153, 153, 153, 152, 151, 149, 148, 146, 145, 144,
       143, 142, 142, 141, 141, 141, 140, 141, 142, 143, 146, 148, 152,
       155, 157, 160, 163, 165, 168, 169, 171, 172, 172, 173, 173, 174,
       175, 177, 178, 179, 179, 179, 178, 178, 178, 178, 179, 180, 180,
       180, 180, 180, 179, 179, 180, 180, 181, 181, 182, 183, 183, 183,
       183, 183, 183, 183, 183, 183, 183, 183, 183, 183, 183, 184, 185,
       185, 185, 184, 184, 183, 183, 184, 185, 185, 186, 186, 186, 186,
       186, 186, 187, 187, 188, 188, 188, 188, 188, 188, 189, 189, 190,
       190, 191, 191, 192, 192]

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
plt.title("Pin Hole 1ns Further Along Beam")
ax = plt.gca()
ax.set_xticks(np.arange(0, 200e-9 + 20e-9, 20e-9))
ax.set_xticklabels([f"{int(x*1e9)} ns" for x in np.arange(0, 200e-9 + 20e-9, 20e-9)])
plt.legend()
plt.show()
