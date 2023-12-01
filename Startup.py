import subprocess
import pathlib
from aiohttp import web
import argparse
import asyncio

#########################################################################
#AIOHTTP
def startTestHandler(request):
    process = subprocess.Popen(PICO_TALKER_START, stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    



REPO_PICO_TALKER_PATH = "Thermal Control/Pico_Talker/Pico_Talker.py"
curr_path = pathlib.Path.cwd()

GIT_REPO_NAME = "Capstone_NEU_inPLane_ThermalCond"
TEST_START_ENDPOINT = "/test-start"

REPO_BASE_PATH = None

for i, parent in enumerate(reversed(curr_path.as_posix().split('/'))): #Get the base path of the repo repository so that relative paths in the repo can be used
    print(parent, i)
    if parent == GIT_REPO_NAME:
        if i == 0:
            REPO_BASE_PATH = curr_path
        else:
            REPO_BASE_PATH = curr_path.parents[i]
        print(REPO_BASE_PATH)
        break

if REPO_BASE_PATH is None:
    raise FileNotFoundError ("Startup file not in proper git directory")

ABS_PICO_TALKER_PATH = str(REPO_BASE_PATH / REPO_PICO_TALKER_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--startup-port", default=3002)
    parser.add_argument("--database", default="your_database.db")
    parser.add_argument("--serial-port", default=None, help="Serial port that the Raspberry Pi Pico PCB is connected to")
    parser.add_argument("--baudrate", default=115200, help="Baud rate the Raspberry Pi Pico PCB communicates with")
    args = parser.parse_args()
    STARTUP_PORT = args.startup_port
    DATABASE_PATH = args.database
    PCB_SERIAL_PORT = args.serial_port
    PCB_BAUD_RATE = args.baudrate

    pico_talker_args = {
        "--database": DATABASE_PATH,
        "--port": PCB_SERIAL_PORT,
        "--baud": PCB_BAUD_RATE
    }

    pico_talker_arg_str = " ".join([str(i) for row in [(key, pico_talker_args[key]) for key in pico_talker_args.keys() if pico_talker_args[key] is not None] for i in row])
    
    PICO_TALKER_START = f'python ""{ABS_PICO_TALKER_PATH}"" {pico_talker_arg_str}'
    print(PICO_TALKER_START)
    loop = asyncio.get_event_loop()
    app = web.Application()
    app.add_routes([
        web.put(TEST_START_ENDPOINT, startTestHandler)
    ])
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, 'localhost', port = STARTUP_PORT)
    asyncio.ensure_future(site.start())
    loop.run_forever()