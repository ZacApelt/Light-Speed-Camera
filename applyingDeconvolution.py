import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter, freqz
from scipy.fft import fft, ifft
import math
import time
import csv

signal =  [211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211,
       211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211,
       211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211,
       211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211,
       211, 211, 210, 210, 210, 209, 208, 207, 204, 200, 195, 190, 184,
       178, 172, 167, 161, 157, 154, 152, 151, 151, 152, 153, 155, 156,
       157, 158, 158, 156, 152, 146, 137, 126, 115, 103,  92,  80,  70,
        61,  54,  49,  47,  46,  46,  46,  46,  47,  47,  48,  49,  50,
        51,  52,  54,  55,  57,  59,  62,  64,  66,  69,  71,  74,  77,
        79,  82,  85,  87,  89,  91,  93,  95,  97,  98,  99, 100, 101,
       103, 104, 105, 107, 109, 111, 114, 116, 119, 122, 125, 128, 131,
       134, 137, 140, 144, 147, 150, 153, 156, 159, 163, 167, 170, 173,
       176, 179, 181, 183, 184, 184, 184, 183, 182, 182, 182, 182, 182,
       183, 184, 185, 187, 189, 191, 192, 192, 192, 191, 191, 190, 190,
       189, 189, 188, 188, 188, 188, 189, 189, 189, 188, 188, 188, 188,
       187, 186, 185, 184, 183, 181, 180, 178, 177, 176, 175, 174, 175,
       175, 176, 176, 176, 176, 176, 176, 176, 175, 175, 175, 174, 174,
       174, 173, 172, 172, 171, 170, 170, 170, 171, 171, 172, 173, 175,
       178, 180, 183, 185, 186, 188, 189, 190, 191, 191, 190, 189, 189,
       188, 188, 189, 189, 190, 192, 193, 195, 197, 198, 199, 200, 200,
       200, 201, 200, 199, 198, 197, 196, 195, 195, 194, 194, 194, 194,
       195, 196, 197, 199, 200, 201, 201, 201, 201, 201, 201, 201, 200,
       200, 199, 199, 198, 198, 199, 199, 199, 199, 198, 197, 197, 197,
       196, 196, 196, 196, 196, 196, 197, 198, 199, 200, 200, 200, 200,
       201, 201, 201, 202, 202, 202, 202, 202, 202, 202, 202, 202, 202,
       202, 202, 202, 202, 201, 201, 201, 201, 201, 201, 200, 200, 200,
       200, 200, 200, 200, 201, 201, 201, 202, 202, 202, 203, 203, 203,
       202, 202, 201, 201, 200, 200, 199, 199, 199, 199, 199, 199, 200,
       201, 201, 201, 202, 202, 202, 203, 203, 203, 204, 204, 204, 204,
       204, 204, 204, 204, 204, 204, 203, 202, 202, 201, 201, 200, 201,
       200, 200, 200, 200, 201, 201, 201, 201, 201, 200]

# signal is the 2nd row of "./scope captures/beamdumpvsnobeamdump.csv"

signal = []
with open("./scope captures/beamdumpvsnobeamdump.csv", "r") as f:
    reader = csv.reader(f)
    rows = list(reader)
    for row in rows:
        signal.append(int(row[2]))

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

# this gives a nice response on the tail end of the signal
num_5_10 = [-0.01189, 0.0284, -0.02741, 0.02193, 0.008951, 0.03094]
den_5_10 = [1, -3.378, 4.855, -3.988, 2.211, -1.092, 0.7669, -0.8181, 0.9332, -0.7089, 0.2251]

# this is a simpler version with less tail end gain
num_5_7 = [-0.01189, 0.02881, -0.02881, 0.02377, 0.007436, 0.03042]
den_5_7 = [1, -3.412, 5.007, -4.266, 2.494, -1.208, 0.5407, -0.1505]


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


def inverse_filter_regularised(y, b, a, alpha=0.05):
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

# x_est_fast = inverse_filter_regularised(signal, fast_num, fast_den)
# x_est_slow = inverse_filter_regularised(signal, slow_num, slow_den)
x_est_5_10 = inverse_filter_regularised(signal, num_5_10, den_5_10)
x_est_5_7 = inverse_filter_regularised(signal, num_5_7, den_5_7)

plt.plot(t, signal, label='Original Signal', color='green')
# plt.plot(t, x_est_fast, label='Fast Deconvolution', color='orange')
# plt.plot(t, x_est_slow, label='Slow Deconvolution', color='blue')
plt.plot(t, x_est_5_10, label='5-10 Deconvolution', color='red')
plt.plot(t, x_est_5_7, label='5-7 Deconvolution', color='purple')
plt.xlabel("Time (s)")
plt.ylabel("Signal")
plt.title("Pin Hole 1ns Further Along Beam")
plt.legend()
plt.show()
