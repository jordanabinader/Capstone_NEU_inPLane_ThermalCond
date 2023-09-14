import numpy as np

def get_fft_data(output, sf):
    # Calculate the FFT of the input signal 'output'
    test = np.fft.fft(output)

    # Get the length of the FFT result
    test_len = len(test)

    # Calculate the one-sided spectrum (ignoring negative frequencies)
    P2 = np.abs(test / test_len)

    # Double the values (except for DC and Nyquist frequencies)
    intensity = P2[:test_len // 2 + 1]
    intensity[1:-1] = 2 * intensity[1:-1]

    # Create a frequency array corresponding to the FFT result
    frequency = (sf) * np.arange(test_len // 2 + 1) / test_len

    # Return the frequency and intensity arrays
    return frequency, intensity

def fit_function(x, a, b, c, temp):
    return a + b * np.sin(2 * np.pi * temp * (x + c))