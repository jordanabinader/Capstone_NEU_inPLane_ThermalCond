#
# Copyright (C) 2019 Pico Technology Ltd. See LICENSE file for terms.
#
# TC-08 STREAMING MODE EXAMPLE


import atexit
import ctypes
import numpy as np
import time
from picosdk.usbtc08 import usbtc08 as tc08
from picosdk.functions import assert_pico2000_ok

#This is incredibly helpful: https://www.picotech.com/download/manuals/usb-tc08-thermocouple-data-logger-programmers-guide.pdf

#this ensures that if the script exists for whatever reason, the tc-08 is properly disconnected from the computer
# so that the next time the script starts there are no errors throw because the device is already connected to another script
def exit_handler():
    status["stop"] = tc08.usb_tc08_stop(chandle)
    assert_pico2000_ok(status["stop"])

    # close unit
    status["close_unit"] = tc08.usb_tc08_close_unit(chandle)
    assert_pico2000_ok(status["close_unit"])

atexit.register(exit_handler)
# Create chandle and status ready for use
chandle = ctypes.c_int16()
status = {}

# open unit
status["open_unit"] = tc08.usb_tc08_open_unit()
assert_pico2000_ok(status["open_unit"])
chandle = status["open_unit"]

# set mains rejection to 50 Hz
status["set_mains"] = tc08.usb_tc08_set_mains(chandle,0)
assert_pico2000_ok(status["set_mains"])

# set up channel
# therocouples types and int8 equivalent
# B=66 , E=69 , J=74 , K=75 , N=78 , R=82 , S=83 , T=84 , ' '=32 , X=88 
typeK = ctypes.c_int8(75)
status["set_channel"] = tc08.usb_tc08_set_channel(chandle, 1, typeK)
assert_pico2000_ok(status["set_channel"])
print("set channel good")

# get minimum sampling interval in ms
status["get_minimum_interval_ms"] = tc08.usb_tc08_get_minimum_interval_ms(chandle)
assert_pico2000_ok(status["get_minimum_interval_ms"])

# set tc-08 running
status["run"] = tc08.usb_tc08_run(chandle, status["get_minimum_interval_ms"])
assert_pico2000_ok(status["run"])
# print("Run Good")
time.sleep(2)

# collect data 
temp_buffer = (ctypes.c_float * 2 * 15)()
times_ms_buffer = (ctypes.c_int32 * 15)()
overflow = ctypes.c_int16()
status["get_temp"] = tc08.usb_tc08_get_temp(chandle, ctypes.byref(temp_buffer), ctypes.byref(times_ms_buffer), 15, ctypes.byref(overflow), 1, 0, 1)
assert_pico2000_ok(status["get_temp"])
time.sleep(1)
# stop unit
status["stop"] = tc08.usb_tc08_stop(chandle)
assert_pico2000_ok(status["stop"])

# close unit
status["close_unit"] = tc08.usb_tc08_close_unit(chandle)
assert_pico2000_ok(status["close_unit"])

# display status returns
print(status)

#My addition to convert the ctypes arrays to numpy arrays
temps = np.ndarray((30, ), 'f', temp_buffer, order='C')
times = np.ndarray((15, ), np.int32, times_ms_buffer, order='C')
print(temps)
print(times)

