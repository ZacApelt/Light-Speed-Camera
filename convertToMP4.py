import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy.signal import lfilter, freqz
from scipy.fft import fft, ifft
import math
import time

saved_vid = np.load("C:/Users/remoteaccess/Downloads/video6.npy")

# the order of every other row is reversed, so we need to flip those rows to get the correct order
for y in range(len(saved_vid)):
    if y % 2 == 1:
        saved_vid[y, :, :] = np.flip(saved_vid[y, :, :], axis=0)

# the signal is inverted, so we need to invert it back
#saved_vid = -saved_vid + saved_vid.max()
    #signal = signal / np.max(np.abs(signal)) + 1
saved_vid = -saved_vid / np.max(np.abs(saved_vid)) + 1

# if any pixels == 1, set it to 0
saved_vid[saved_vid == 1] = 0
# renormalize the video to be between 0 and 1
#saved_vid = (saved_vid - np.min(saved_vid)) / (np.max(saved_vid) - np.min(saved_vid))

print(saved_vid[0, 0, :])

# video is flipped upside down, so we need to flip it back
saved_vid = np.flip(saved_vid, axis=0)

# remove last 100 samples from each pixel's waveform to remove the tail
saved_vid = saved_vid[:, :, :-100]

# this gives a nice response on the tail end of the signal
num_5_10 = [-0.01189, 0.0284, -0.02741, 0.02193, 0.008951, 0.03094]
den_5_10 = [1, -3.378, 4.855, -3.988, 2.211, -1.092, 0.7669, -0.8181, 0.9332, -0.7089, 0.2251]

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

deconv_video = np.zeros_like(saved_vid)

# # apply the deconvolution to each pixel's waveform
for y in range(len(saved_vid)):
    for x in range(len(saved_vid[0])):
        signal = saved_vid[y, x, :]
        #print(signal)
        deconv_signal = inverse_filter_regularised(signal, num_5_10, den_5_10)
        #print(deconv_signal)
        deconv_signal[deconv_signal < 0] = 0
        deconv_video[y, x, :] = deconv_signal
        

def save_video_safe(video, filename, fps=30):

    # apply a gaussian filter on each frame to smooth it out spacially
    for i in range(video.shape[2]):
        video[:, :, i] = cv2.GaussianBlur(video[:, :, i], (3, 3), 0)
    

    vmin = np.percentile(video, 1)
    vmax = np.percentile(video, 99) 

    if vmax <= vmin:
        vmax = vmin + 1

    vid = np.clip((video - vmin) / (vmax - vmin), 0, 1)
    vid = (255 * vid).astype(np.uint8)

    h, w, n = vid.shape

    # MP4 prefers even dimensions
    if h % 2:
        vid = np.pad(vid, ((0,1),(0,0),(0,0)))
        h += 1
    if w % 2:
        vid = np.pad(vid, ((0,0),(0,1),(0,0)))
        w += 1

    writer = cv2.VideoWriter(
        filename,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h),
        isColor=True
    )

    if not writer.isOpened():
        raise RuntimeError("VideoWriter failed to open. Try AVI/XVID instead.")

    for i in range(n):
        frame = cv2.cvtColor(vid[:, :, i], cv2.COLOR_GRAY2BGR)
        writer.write(frame)

    writer.release()
    print("Saved:", filename)

save_video_safe(saved_vid, "scan12.mp4", fps=5)
save_video_safe(deconv_video, "scan12_deconv.mp4", fps=5)