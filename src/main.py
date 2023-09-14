import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import utils

if __name__ == "__main__":
    opAmpFrequency = input('Enter opAmp frequency: ') #0.02 Hardcoded value
    filename = f'C:\\Users\\evanz\\OneDrive - Northeastern University\\DAPS\\Diffusivity Testing\\highAmp_AlSheet_5mm_TC34_L=0.72cm_10msSample_f={opAmpFrequency}.plw'
    t, Temps, param = PLW2MLv5(filename)

    samplingRate = 1 / 0.01  # 1/sample period (seconds) in omega software
    TempFrequency = opAmpFrequency * 2
    tcdata = np.column_stack((t / 1000, Temps))

    # User input for which TC to use
    TCidentity = [3, 4]  # For multi-sample data files, number corresponds to TC# in measurement

    for i in range(1, tcdata.shape[1]):
        tcdata[:, i] = tcdata[:, i] - np.convolve(tcdata[:, i], np.ones(samplingRate // TempFrequency), mode='same') / (samplingRate // TempFrequency)

    plt.plot(tcdata[:, 0], tcdata[:, TCidentity[0] + 1], tcdata[:, 0], tcdata[:, TCidentity[1] + 1])
    [t, T] = plt.ginput()
    t = np.round(t)

    # Fit data
    Fit1_params, _ = curve_fit(utils.fit_function, tcdata[t[0] * samplingRate:t[1] * samplingRate, 0], tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[0] + 1], p0=[np.mean(tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[0] + 1]), np.max(tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[0] + 1]) - np.mean(tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[0] + 1]), np.pi])
    Fit2_params, _ = curve_fit(utils.fit_function, tcdata[t[0] * samplingRate:t[1] * samplingRate, 0], tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[1] + 1], p0=[np.mean(tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[1] + 1]), np.max(tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[1] + 1]) - np.mean(tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[1] + 1]), np.pi])

    phaseShifts = [Fit1_params[2], Fit2_params[2]]
    
    # Continue with the remaining calculations
    M = 2 * Fit1_params[1]
    N = 2 * Fit2_params[1]
    period = 1 / TempFrequency
    
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

   
    L = input('Enter the distance between thermocouples in cm: ') # 0.72  Hardcoded value

    diffusivity = L**2 / (2 * delta_time * np.log(M / N))
    print(f'R^2, Thermocouple 1 = {Fit1_params[2]}')
    print(f'R^2, Thermocouple 2 = {Fit2_params[2]}')

    plt.plot(tcdata[t[0] * samplingRate:t[1] * samplingRate, 0], tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[0] + 1],
             tcdata[t[0] * samplingRate:t[1] * samplingRate, 0], utils.fit_function(tcdata[t[0] * samplingRate:t[1] * samplingRate, 0], *Fit1_params),
             tcdata[t[0] * samplingRate:t[1] * samplingRate, 0], tcdata[t[0] * samplingRate:t[1] * samplingRate, TCidentity[1] + 1],
             tcdata[t[0] * samplingRate:t[1] * samplingRate, 0], utils.fit_function(tcdata[t[0] * samplingRate:t[1] * samplingRate, 0], *Fit2_params))
    plt.pause(2)

    # Continue with any additional code or functions as needed
