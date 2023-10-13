import atexit
import ctypes
import time
from picosdk.usbtc08 import usbtc08 as tc08
from picosdk.functions import assert_pico2000_ok
import matplotlib.pyplot as plt
import pandas as pd
from collections import deque

MAX_LIST_SIZE = 1000  # Limit for values in python list, ~1,000,000
MAX_GRAPH_BUFFER = 50  # Limit amount of data points to be graphed, ~10,000
SLEEP_TIME = 1  # How long is the delay between cycles in s, ~1
NUM_CYCLES = 50  # How many cycles should be run, used in debugging with for loop

# -------IMPORTANT-------
# library_path in venv/lib/python3.9/sitepackages/picosdk/library.py
# should point to position of installed libusbtc08 file
# for example:
# def _load(self):
#   library_path = '/Library/Frameworks/PicoSDK.framework/Libraries/libusbtc08/libusbtc08.dylib'


def exit_handler():
    status["stop"] = tc08.usb_tc08_stop(chandle)
    assert_pico2000_ok(status["stop"])

    # close unit
    status["close_unit"] = tc08.usb_tc08_close_unit(chandle)
    assert_pico2000_ok(status["close_unit"])


# Disconnect TC08 if program halts before proper closing
atexit.register(exit_handler)

# Create chandle and status ready for use
chandle = ctypes.c_int16()
status = {}

# open unit
status["open_unit"] = tc08.usb_tc08_open_unit()
assert_pico2000_ok(status["open_unit"])
chandle = status["open_unit"]

# set mains rejection to 50 Hz
status["set_mains"] = tc08.usb_tc08_set_mains(chandle, 0)
assert_pico2000_ok(status["set_mains"])

# set up channel
# thermocouples types and int8 equivalent
# B=66 , E=69 , J=74 , K=75 , N=78 , R=82 , S=83 , T=84 , ' '=32 , X=88
typeK = ctypes.c_int8(75)
status["set_channel"] = tc08.usb_tc08_set_channel(chandle, 1, typeK)
tc08.usb_tc08_set_channel(chandle, 2, typeK)
assert_pico2000_ok(status["set_channel"])

# get minimum sampling interval in ms
status["get_minimum_interval_ms"] = tc08.usb_tc08_get_minimum_interval_ms(chandle)
assert_pico2000_ok(status["get_minimum_interval_ms"])

# set tc-08 running
status["run"] = tc08.usb_tc08_run(chandle, status["get_minimum_interval_ms"])
assert_pico2000_ok(status["run"])

# initialize ctype buffers
temp_buffer = (ctypes.c_float * 15)()
times_ms_buffer = (ctypes.c_int32 * 15)()
overflow = ctypes.c_int16()

temp_buffer2 = (ctypes.c_float * 15)()
times_ms_buffer2 = (ctypes.c_int32 * 15)()
overflow2 = ctypes.c_int16()

# Initialize live plot
plt.ion()  # Turn on interactive mode for Matplotlib
fig, ax = plt.subplots()
ax.set_xlabel('Time (s)')
ax.set_ylabel('Temperature (°C)')
line, = ax.plot([], [], 'r-', label='Channel 1')
line2, = ax.plot([], [], 'b-', label='Channel 2')
ax.legend(loc='upper left')

# create lists to temporarily store data
temps = []
times = []
temps2 = []
times2 = []

# create deques to temporarily store data for graphing
temps_graphing = deque(maxlen=MAX_GRAPH_BUFFER)
times_graphing = deque(maxlen=MAX_GRAPH_BUFFER)
temps2_graphing = deque(maxlen=MAX_GRAPH_BUFFER)
times2_graphing = deque(maxlen=MAX_GRAPH_BUFFER)

# Define Dataframes to store data
df1 = pd.DataFrame({'Time (s)': times, 'Temperature (°C) - Channel 1': temps})
df2 = pd.DataFrame({'Time (s)': times2, 'Temperature (°C) - Channel 2': temps2})

# loop to collect data
for i in range(NUM_CYCLES):
    time.sleep(SLEEP_TIME)

    # clear buffers
    ctypes.memset(temp_buffer, 0, ctypes.sizeof(temp_buffer))
    ctypes.memset(temp_buffer2, 0, ctypes.sizeof(temp_buffer2))
    ctypes.memset(times_ms_buffer, 0, ctypes.sizeof(times_ms_buffer))
    ctypes.memset(times_ms_buffer2, 0, ctypes.sizeof(times_ms_buffer2))

    # collect data
    status["get_temp"] = tc08.usb_tc08_get_temp_deskew(chandle, ctypes.byref(temp_buffer),
                                                       ctypes.byref(times_ms_buffer), 15, ctypes.byref(overflow),
                                                       1, 0, 1)
    tc08.usb_tc08_get_temp_deskew(chandle, ctypes.byref(temp_buffer2),
                                  ctypes.byref(times_ms_buffer2), 15,
                                  ctypes.byref(overflow2), 2, 0, 1)
    assert_pico2000_ok(status["get_temp"])

    # record data
    for j in range(len(temp_buffer)):
        if temp_buffer[j] != 0:
            temps.append(temp_buffer[j])
            times.append(times_ms_buffer[j] / 1000.0)  # Convert time to seconds
            temps_graphing.append(temp_buffer[j])
            times_graphing.append(times_ms_buffer[j] / 1000.0)

    for j in range(len(temp_buffer2)):
        if temp_buffer2[j] != 0:
            temps2.append(temp_buffer2[j])
            times2.append(times_ms_buffer2[j] / 1000.0)  # Convert time to seconds
            temps2_graphing.append(temp_buffer2[j])
            times2_graphing.append(times_ms_buffer2[j] / 1000.0)

    # Check if the list sizes exceed a threshold (e.g., 1,000,000 entries)
    if len(temps) >= MAX_LIST_SIZE:
        # Store data from temps, times lists to dataframe, clears lists after
        if temps:
            df1 = pd.concat([df1, pd.DataFrame({'Time (s)': times,
                                                'Temperature (°C) - Channel 1': temps})], ignore_index=True)
        if temps2:
            df2 = pd.concat([df2, pd.DataFrame({'Time (s)': times2,
                                                'Temperature (°C) - Channel 2': temps2})], ignore_index=True)
        temps.clear()
        times.clear()
        temps2.clear()
        times2.clear()

    # Update the live plot
    # TODO Should be taken out of this loop, run in parallel thread?
    line.set_data(times_graphing, temps_graphing)
    line2.set_data(times2_graphing, temps2_graphing)
    ax.relim()
    ax.autoscale_view()
    plt.pause(0.1)

# After the loop, transfer any remaining data to the DataFrame
if temps:
    df1 = pd.concat([df1, pd.DataFrame({'Time (s)': times,
                                        'Temperature (°C) - Channel 1': temps})], ignore_index=True)
if temps2:
    df2 = pd.concat([df2, pd.DataFrame({'Time (s)': times2,
                                        'Temperature (°C) - Channel 2': temps2})], ignore_index=True)
temps.clear()
times.clear()
temps2.clear()
times2.clear()

# Stop unit - Commented out due to exit handler
# status["stop"] = tc08.usb_tc08_stop(chandle)
# assert_pico2000_ok(status["stop"])

# Close unit
# status["close_unit"] = tc08.usb_tc08_close_unit(chandle)
# assert_pico2000_ok(status["close_unit"])

# Keep the plot open
plt.ioff()
plt.show()

# Display status returns
print(status)

# export to csv
df1.to_csv('channel1_data.csv', index=False)
df2.to_csv('channel2_data.csv', index=False)