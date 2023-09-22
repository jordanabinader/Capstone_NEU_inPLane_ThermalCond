import numpy as np
import pandas as pd
import pycotech
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from scipy.signal import convolve
from scipy.stats import linregress

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

def read_plw_to_pandas(plw_file):
  """Reads a PicoLog PLW file into a Pandas DataFrame.

  Args:
    plw_file: The path to the PLW file.

  Returns:
    A Pandas DataFrame containing the data from the PLW file.
  """

  # Read the PLW file using pycotech.
  df = pycotech.utils.read_plw(plw_file)

  # Convert the pycotech DataFrame to a Pandas DataFrame.
  df = pd.DataFrame(df)

  return df

def read_csv_to_pandas(csv_file):
  # Read the CSV file into a pandas DataFrame.
  try:
      df = pd.read_csv(csv_file)
  except FileNotFoundError:
      print(f"{csv_file} not found.")
  except Exception as e:
      print(f"An error occurred: {str(e)}")
  return df

# Define the model function
def sinusoidal_model(x, b0, b1, b2, TempFrequency):
  return b0 + b1 * np.sin(2 * np.pi * TempFrequency * (x + b2))

# Non-linear fitting
def fit_data(tcdata, index, samplingRate, TempFrequency, t):

  x_data = tcdata[int(t[0] * samplingRate):int(t[1] * samplingRate), 0]
 
  y_data = tcdata[int(t[0] * samplingRate):int(t[1] * samplingRate), index]

  if len(x_data) != len(y_data) or len(x_data) == 0 or len(y_data) == 0:
    raise ValueError("x_data and y_data must have the same non-zero length")

  # initial guess
  p0 = [np.mean(y_data), np.max(y_data) - np.mean(y_data), np.pi]

  if len(p0) != 3:  # Assuming your model has 3 parameters
    raise ValueError("Initial parameter vector p0 must have length 3")

  # Define a lambda function to pass TempFrequency as an additional parameter
  model_func = lambda x, a, b, phi: sinusoidal_model(x, a, b, phi, TempFrequency)
    
  try:  
      popt, _ = curve_fit(model_func, x_data, y_data, p0=p0)  # fit the model
  except Exception as e:
      raise RuntimeError(f"Curve fitting failed with error: {str(e)}")
  
  # Calculate the adjusted R-squared
  _, _, r_value, _, _ = linregress(x_data, y_data)
  r_squared = r_value**2
  n = len(x_data)
  p = len(p0)  # number of parameters in the model
  adjusted_r_squared = 1 - (1 - r_squared) * ((n - 1) / (n - p - 1))

  return popt, adjusted_r_squared  # return phase shift (phi)

def process_and_plot_tcdata(tcdata, samplingRate, TempFrequency, TCidentity):
  """
  Process and Plot tcdata.

  Parameters:
  tcdata (np.array): 2D array of thermocouple data.
  samplingRate (int): The sampling rate of the data.
  TempFrequency (int): The temperature frequency of the data.
  TCidentity (list): A list containing the indices of the thermocouples to plot.

  Returns:
  np.array: Processed tcdata.
  """
  window_size = int(samplingRate // TempFrequency)

  for i in range(1, tcdata.shape[1]):
    # Calculate the moving average
    column_series = pd.Series(tcdata[:, i])
    moving_avg = column_series.rolling(window=window_size, min_periods=1, center=True).mean()
    tcdata[:, i] = column_series - moving_avg

  # Plotting the processed tcdata
  plt.plot(tcdata[:, 0], tcdata[:, TCidentity[0]], label=f'TC{TCidentity[0]+1}')
  plt.plot(tcdata[:, 0], tcdata[:, TCidentity[1]], label=f'TC{TCidentity[1]+1}')
  plt.legend()
 
  return tcdata

def fitted_plot_data(tcdata, t, samplingRate, TCidentity, fitted1, fitted2, frequency):
  """
  Plots multiple sets of x, y data on the same graph.
    
  :param tcdata: 2D array representing the data
  :param t: Tuple representing the start and end times
  :param samplingRate: Sampling rate of the data
  :param TCidentity: List containing the indices to be used from tcdata
  :param fitted1: 1D array representing the first set of fitted data
  :param fitted2: 1D array representing the second set of fitted data
  """
  # extract the required range from tcdata
  t1 = int(t[0] * samplingRate)
  t2 = int(t[1] * samplingRate)
    
  x_data_1 = tcdata[t1:t2, 0]
  y_data_1 = tcdata[t1:t2, TCidentity[0]]
  a1, b1, c1 = fitted1
  y_fitted1 = a1 + b1 * np.sin(2 * np.pi * frequency * (x_data_1 + c1))
    
  x_data_2 = tcdata[t1:t2, 0]
  y_data_2 = tcdata[t1:t2, TCidentity[1]]
  a2, b2, c2 = fitted2
  y_fitted2 = a2 + b2 * np.sin(2 * np.pi * frequency * (x_data_1 + c2))

  plt.plot(x_data_1, y_data_1, label='Data 1')
  plt.plot(x_data_1, y_fitted1, label='Fitted 1')
  plt.plot(x_data_2, y_data_2, label='Data 2')
  plt.plot(x_data_2, y_fitted2, label='Fitted 2')
    
  plt.legend()
  plt.show()

