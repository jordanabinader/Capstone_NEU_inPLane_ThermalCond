import numpy as np
import matplotlib.pyplot as plt
import utils as ut
import time
import sqlite3

MAX_GRAPH_BUFFER = 100000  # Limit amount of data points to be graphed, ~100,000
TC_TIME_SHIFT = 0.68  # Time difference between TCs
SLEEP_TIME = 1
DENSITY = 1
SPECIFIC_HEAT = 1
L = .72
OPAMP_FREQUENCY = .001  # 1/OpAmp Period, .001 for csv
SAMPLING_RATE = 1 / 0.01  # 1/.01 for csv, 1/.2 for daq (I think?)
TEMP_FREQUENCY = float(OPAMP_FREQUENCY) * 2  # What is this for? Probably remove later
DATABASE_NAME = 'your_database.db'
TABLE_NAME = "Data1"

# Connect to the database
conn = sqlite3.connect(DATABASE_NAME)

# Create a cursor
cursor = conn.cursor()

# create deques to temporarily store data for graphing, analysis
times1 = []
times2 = []
temps1 = []
temps2 = []

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
# samplingRate = 1 / 0.01  # 1/sample period (seconds) in omega software

while 1:
    time.sleep(SLEEP_TIME)

    cursor.execute(f'''SELECT relTime, temp1, temp2
                      FROM {TABLE_NAME}
                      ORDER BY relTime DESC
                      LIMIT ?''', (MAX_GRAPH_BUFFER,))

    results = cursor.fetchall()

    time.sleep(1)

    # Add data
    times1 = [row[0] for row in results]
    temps1 = [row[1] for row in results]
    temps2 = [row[2] for row in results]

    # Fix timing for temps2
    times2 = [x+TC_TIME_SHIFT for x in times1]

    # Data pre-processing for noise-reduction, signal smoothing, normalization by removing moving average
    temps1_pr = ut.process_data(temps1, SAMPLING_RATE, TEMP_FREQUENCY)
    temps2_pr = ut.process_data(temps2, SAMPLING_RATE, TEMP_FREQUENCY)

    # User input for points selection
    # points = np.round(np.array(plt.ginput(2))[:, 0])
    # points = [2000, 4000]
    # plt.close()
    # print(f'Time interval chosen = {points}')

    params1, adjusted_r_squared1 = ut.fit_data(temps1_pr, times1, TEMP_FREQUENCY)
    params2, adjusted_r_squared2 = ut.fit_data(temps2_pr, times2, TEMP_FREQUENCY)
    phaseShifts = [params1[2], params2[2]]

    # Continue with the remaining calculations
    M = 2 * params1[1]
    N = 2 * params2[1]
    period = 1 / TEMP_FREQUENCY

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

    phaseDifference = abs(phaseShifts[1] - phaseShifts[0])  # From wave mechanics -
    # same frequency but different additive constants
    # so the phase difference is just the difference of the individual phase shifts
    phaseDifference = phaseDifference % period

    delta_time = phaseDifference

    # L = float(input('Enter the distance between thermocouples in cm: '))  # 0.72  Hardcoded value

    diffusivity = L ** 2 / (2 * delta_time * np.log(M / N))

    conductivity = diffusivity * DENSITY * SPECIFIC_HEAT

    print("")
    print(delta_time)

    print(f'R^2, Thermocouple 1 = {adjusted_r_squared1}')
    print(f'R^2, Thermocouple 2 = {adjusted_r_squared2}')
    print(f'Diffusivity = {diffusivity}')
    print(f'T. Conductivity = {conductivity}')

    line.set_data(times1, temps1_pr)
    line2.set_data(times2, temps2_pr)

    a1, b1, c1 = params1
    y_fitted1 = a1 + b1 * np.sin(2 * np.pi * TEMP_FREQUENCY * (times1 + c1))

    a2, b2, c2 = params2
    y_fitted2 = a2 + b2 * np.sin(2 * np.pi * TEMP_FREQUENCY * (times2 + c2))

    # TODO plot lines for M, N, delta_time

    lineF.set_data(times2, y_fitted1)
    line2F.set_data(times2, y_fitted2)

    ax.relim()
    ax.autoscale_view()
    plt.pause(0.1)

    end_time = time.time()

plt.ioff()
plt.show()

# Close the cursor and the connection
cursor.close()
conn.close()
