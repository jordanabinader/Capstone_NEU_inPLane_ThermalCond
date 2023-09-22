import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import convolve
import utils.utils_first as ut

if __name__ == "__main__":

    directory = "AlStrip_TC34_10msSampling_MountedTCs_L=0.71cm_TIMpaste_24VCPUFan_f=0.001.plw_1.csv"

    raw_df = ut.read_csv_to_pandas(directory)

    opAmpFrequency = input('Enter opAmp frequency: ') #0.02 Hardcoded value

    samplingRate = 1 / 0.01  # 1/sample period (seconds) in omega software

    # Add the time column with actual time interval and cumsum
    raw_df['time'] = 0.01

    raw_df['time'] =  raw_df['time'].cumsum()

    time, temps = raw_df['time'], raw_df[['TC3', 'TC4']] # API or file name socket

    tempFrequency = float(opAmpFrequency) * 2

    tcdata = np.column_stack((time, temps)) # TODO: Why would you devide t / 1000?

    # User input for which TC to use
    TCidentity = [1, 2]  # For multi-sample data files, number corresponds to TC# in measurement

    # Data pre-processing for noise-reduction, signal smoothing, normalization by removing moving average
    tcdata = ut.process_and_plot_tcdata(tcdata, samplingRate, tempFrequency, TCidentity)

    # User input for points selection
    points = np.round(np.array(plt.ginput(2))[:, 0])

    print(points)
    params1, adjusted_r_squared1 = ut.fit_data(tcdata, TCidentity[0], samplingRate, tempFrequency, points)
    params2, adjusted_r_squared2 = ut.fit_data(tcdata, TCidentity[1], samplingRate, tempFrequency, points)
    phaseShifts = [params1[2], params2[2]]
    
    # Continue with the remaining calculations
    M = 2 * params1[1]
    N = 2 * params2[1]
    period = 1 / tempFrequency
    
    if M < 0:
        phaseShifts[0] = phaseShifts[0] + period / 2
        M = -M
    
    if N < 0:
        phaseShifts[1] = phaseShifts[1] + period / 2
        N = -N  
    
    # Reduce first phase shift to the very first multiple to the right of t=0
    if phaseShifts[0] > 0:
        while phaseShifts[0] > 0:
            phaseShifts[0] = phaseShifts[0] - period
    else:
        while phaseShifts[0] < -period:
            phaseShifts[0] = phaseShifts[0] + period
    
    # Reduce 2nd phase shift to the very first multiple to the right of t=0
    if phaseShifts[1] > 0:
        while phaseShifts[1] > 0:
            phaseShifts[1] = phaseShifts[1] - period
    else:
        while phaseShifts[1] < -period:
            phaseShifts[1] = phaseShifts[1] + period
    
    # Add a phase to ensure 2 is after 1 in time
    if phaseShifts[1] > phaseShifts[0]:
        phaseShifts[1] = phaseShifts[1] - period
    
    phaseDifference = abs(phaseShifts[1] - phaseShifts[0])  # From wave mechanics - same frequency but different additive constants so the phase difference is just the difference of the individual phase shifts
    phaseDifference = phaseDifference % period
    
    delta_time = phaseDifference

   
    L = float(input('Enter the distance between thermocouples in cm: ')) # 0.72  Hardcoded value

    diffusivity = L**2 / (2 * delta_time * np.log(M / N))
    print(f'R^2, Thermocouple 1 = {adjusted_r_squared1}')
    print(f'R^2, Thermocouple 2 = {adjusted_r_squared2}')

    ut.fitted_plot_data(tcdata, points, samplingRate, TCidentity, params1, params2, tempFrequency)

