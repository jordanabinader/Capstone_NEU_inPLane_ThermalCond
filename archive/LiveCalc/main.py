import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import utils as ut
import time

MAX_GRAPH_BUFFER = 200000  # Limit amount of data points to be graphed, ~10,000
VALUES_TO_READ = 30000


if __name__ == "__main__":

    directory = "fully_converted_AlStrip_TC34_10msSampling_MountedTCs_L=0.71cm_TIMpaste_24VCPUFan_f=0.001.plw_1.csv"

    # Read the original CSV file
    df = pd.read_csv(directory)
    df = ut.clean_dataframe(df)

    # create lists to store data
    temps = list(df['TC3'])
    times = [i * 0.01 for i in range(len(df))]
    temps2 = list(df['TC4'])
    # times2 = [0.005 + i * 0.01 for i in range(len(df))]
    times2 = [i * 0.01 for i in range(len(df))]

    # create deques to temporarily store data for graphing, analysis
    temps_graphing = []
    times_graphing = []
    temps2_graphing = []
    times2_graphing = []

    # Initialize live plot
    plt.ion()  # Turn on interactive mode for Matplotlib
    fig, ax = plt.subplots()
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Temperature (°C)')
    line, = ax.plot([], [], 'g-', label='Channel 1')
    lineF, = ax.plot([], [], 'r-', label='Channel 1 Fitted')
    line2, = ax.plot([], [], 'y-', label='Channel 2')
    line2F, = ax.plot([], [], 'b-', label='Channel 2 Fitted')
    ax.legend(loc='upper left')

    # opAmpFrequency = input('Enter opAmp frequency: ')  # 0.02 Hardcoded value
    opAmpFrequency = .001

    samplingRate = 1 / 0.01  # 1/sample period (seconds) in omega software

    # df1 = ut.clean_dataframe(df1)
    # df2 = ut.clean_dataframe(df2)

    tempFrequency = float(opAmpFrequency) * 2

    for i in range(0, len(temps), VALUES_TO_READ):
        time.sleep(1)

        start_time = time.time()

        # Add data
        temps_graphing.extend(temps[i:i + VALUES_TO_READ])
        times_graphing.extend(times[i:i + VALUES_TO_READ])
        temps2_graphing.extend(temps2[i:i + VALUES_TO_READ])
        times2_graphing.extend(times2[i:i + VALUES_TO_READ])

        # Emulate capped size deque behavior
        if len(temps_graphing) > MAX_GRAPH_BUFFER:
            temps_graphing = temps_graphing[VALUES_TO_READ::]
            times_graphing = times_graphing[VALUES_TO_READ::]
            temps2_graphing = temps2_graphing[VALUES_TO_READ::]
            times2_graphing = times2_graphing[VALUES_TO_READ::]

        # Data pre-processing for noise-reduction, signal smoothing, normalization by removing moving average
        temps_graphing_pr = ut.process_data(temps_graphing,samplingRate,tempFrequency)
        temps2_graphing_pr = ut.process_data(temps2_graphing,samplingRate,tempFrequency)

        # User input for points selection
        # points = np.round(np.array(plt.ginput(2))[:, 0])
        # points = [2000, 4000]
        # plt.close()
        # print(f'Time interval chosen = {points}')

        params1, adjusted_r_squared1 = ut.fit_data(temps_graphing_pr, times_graphing, tempFrequency)
        params2, adjusted_r_squared2 = ut.fit_data(temps2_graphing_pr, times2_graphing, tempFrequency)
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

        phaseDifference = abs(phaseShifts[1] - phaseShifts[
            0])  # From wave mechanics - same frequency but different additive constants so the phase difference is just the difference of the individual phase shifts
        phaseDifference = phaseDifference % period

        delta_time = phaseDifference

        # L = float(input('Enter the distance between thermocouples in cm: '))  # 0.72  Hardcoded value
        L = .71

        diffusivity = L ** 2 / (2 * delta_time * np.log(M / N))

        density = 1
        specific_heat = 1

        conductivity = diffusivity * density * specific_heat

        print(delta_time)

        print(f'R^2, Thermocouple 1 = {adjusted_r_squared1}')
        print(f'R^2, Thermocouple 2 = {adjusted_r_squared2}')
        print(f'diffusivity = {diffusivity}')
        print(f'conductivity = {conductivity}')

        line.set_data(times_graphing, temps_graphing_pr)
        line2.set_data(times2_graphing, temps2_graphing_pr)

        a1, b1, c1 = params1
        y_fitted1 = a1 + b1 * np.sin(2 * np.pi * tempFrequency * (times_graphing + c1))

        a2, b2, c2 = params2
        y_fitted2 = a2 + b2 * np.sin(2 * np.pi * tempFrequency * (times2_graphing + c2))

        lineF.set_data(times_graphing, y_fitted1)
        line2F.set_data(times2_graphing, y_fitted2)

        ax.relim()
        ax.autoscale_view()
        plt.pause(0.1)

        end_time = time.time()
        elapsed_time = start_time - end_time
        print(f'Elapsed Time: {elapsed_time}')

plt.ioff()
plt.show()