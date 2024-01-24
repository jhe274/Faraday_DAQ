import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import scipy.fftpack

# Specify the folder path
dir_path = os.path.join(os.getcwd(), 'Faraday rotation measurements')
K_vapor = os.path.join(dir_path, 'Data_acquisition')
lockin_path = os.path.join(K_vapor, 'FR_DAQ', 'FieldCrumley', 'Data', 'Lock-ins')

def Lock_ins(file):
    '''
    Read lock-ins data files
    '''
    with open(file, 'r') as f:
        data = pd.read_csv(file, sep=',', header=None, skiprows=9,
                           names=['Timestamp', 'X_mod', 'Y_mod', 'X_2f', 'Y_2f', 'X_dc', 'Y_dc'])

        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        start_time = data['Timestamp'].iloc[0]
        data['Timestamp'] = (data['Timestamp'] - start_time).dt.total_seconds()

        Timestamps = data['Timestamp'].to_numpy()  # [s]
        Xdc = data['X_dc'].to_numpy()
        Ydc = data['Y_dc'].to_numpy()
        X2f = data['X_2f'].to_numpy()
        Y2f = data['Y_2f'].to_numpy()
        Xmod = data['X_mod'].to_numpy()
        Ymod = data['Y_mod'].to_numpy()

    return Timestamps, Xdc, Ydc, X2f, Y2f, Xmod, Ymod

files = ['Faraday_lockins_2024-01-24_2.lvm', 'Faraday_lockins_2024-01-24_3.lvm']

fig, axs = plt.subplots(3, 1, figsize=(10, 8))

for file in files:
    Timestamps, Xdc, Ydc, X2f, Y2f, Xmod, Ymod = Lock_ins(os.path.join(lockin_path, file))

    # Use NumPy element-wise squaring
    Xdc_square = np.abs(Xdc)**2
    Ydc_square = np.abs(Ydc)**2

    # Compute the magnitude using np.abs()
    r_dc = np.abs(Xdc_square + Ydc_square)

    Ndc = Xdc.size
    T = 5E-3  # [ms]

    r_dc_fourier = scipy.fftpack.fft(r_dc)
    xdcf = np.fft.fftfreq(Ndc, T)
    ydcf = np.abs(np.fft.fft(r_dc))

    axs[2].plot(xdcf, ydcf, label=f'dc(R) {file}')

    # '2f' column
    X2f_square = np.abs(X2f)**2
    Y2f_square = np.abs(Y2f)**2
    r_2f = np.abs(X2f_square + Y2f_square)

    N2f = X2f.size
    r_2f_fourier = scipy.fftpack.fft(r_2f)
    x2ff = np.fft.fftfreq(N2f, T)
    y2ff = np.abs(np.fft.fft(r_2f))

    axs[1].plot(x2ff, y2ff, label=f'2f(R) {file}')

    # 'mod' column
    Xmod_square = np.abs(Xmod)**2
    Ymod_square = np.abs(Ymod)**2
    r_mod = np.abs(Xmod_square + Ymod_square)

    Nmod = Xmod.size
    r_mod_fourier = scipy.fftpack.fft(r_mod)
    xmodf = np.fft.fftfreq(Nmod, T)
    ymodf = np.abs(np.fft.fft(r_mod))

    axs[0].plot(xmodf, ymodf, label=f'Mod(R) {file}')

axs[0].set_xlim(0 - (np.max(xmodf)) * (0.01), np.max(xmodf) * (1.01))
axs[0].set_xlabel('Frequency (Hz)')
axs[0].set_ylabel('Amplitude (arbitrary unit)')
axs[0].set_title('FFT, modulating lock in amp')
axs[0].set_xticks(np.arange(0, np.max(xmodf) * 1.01, 10))
axs[0].legend()

axs[1].set_xlim(0 - (np.max(x2ff)) * (0.01), np.max(x2ff) * (1.01))
axs[1].set_xlabel('Frequency (Hz)')
axs[1].set_ylabel('Amplitude (arbitrary unit)')
axs[1].set_title('FFT, 2f lock in amp')
axs[1].set_xticks(np.arange(0, np.max(x2ff) * 1.01, 10))
axs[1].legend()

axs[2].set_xlim(0 - (np.max(xdcf)) * (0.01), np.max(xdcf) * (1.01))
axs[2].set_xlabel('Frequency (Hz)')
axs[2].set_ylabel('Amplitude (arbitrary unit)')
axs[2].set_title('FFT, dc lock in amp')
axs[2].set_xticks(np.arange(0, np.max(xdcf) * 1.01, 10))
axs[2].legend()

plt.tight_layout()
plt.show()
