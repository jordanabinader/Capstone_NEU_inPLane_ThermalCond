import Serial_Helper
import argparse
import re
import asyncio
import serial_asyncio #Tutorial used: https://tinkering.xyz/async-serial/
import aiosqlite
from collections.abc import Iterable
import time
import math
from functools import partial
import aiohttp
import signal
import os

#Variables for use inititializing databases
TEST_DIRECTORY_TABLE_NAME = "test_directory"
POWER_TABLE_NAME_BASE = "power_table" #Base strings for the test specific tables that the test name gets appended to with testNameTableFormatter
TEST_SETTING_TABLE_NAME_BASE = "test_settings" #Base strings for the test specific tables that the test name gets appended to with testNameTableFormatter

TEST_SETTING_TABLE_NAME = "" #Filled in by connectDatabase
POWER_TABLE_NAME = "" #Filled in by connectDatabase
POWER_INITIALIZATION_QUERY = "" #Filled in by connectDatabase
TEST_SETTING_INITIALIZATION_QUERY = "" #Filled in by connectDatabase

#Serial Communication Constants (see Serial Communication Pattern.md)
MSG_LEN = 8
HEATER_NOT_FOUND_ERROR = 0x21
DUTY_CYCLE_CHANGE_HEADER = (0x01, 0x02, 0x03) # Heater 1, Heater 2, Both Heaters
INA260_DATA_HEADER = (0x11, 0x12)
TERMINATION = 0xff
DUTY_CYCLE_UPDATE_PERIOD = 0.5 # Seconds


#Data to be collected and updated from SQLite Database
control_modes_map = {
    "power":0,
    "temperature":1 #Currently not supported
}
control_mode = 0 #see control_modes_map
control_freq = 0.1 #Hz, desired frequency of the output curve whether that is power or temperature
# duty_cycle = [0, 0] #% duty cycle of each heater, useful for ensuring that the power output lines up properly
control_amplitude = 1 #Amplitude, either in Watts or degrees celcius depending on control mode


#For regex searching
ACCEPTABLE_MSG_HEADERS = bytes() #Flatten acceptable headers, for use in parsing serial messages
for h in [DUTY_CYCLE_CHANGE_HEADER, INA260_DATA_HEADER, HEATER_NOT_FOUND_ERROR]:
    if isinstance(h, Iterable):
        for i in h:
            ACCEPTABLE_MSG_HEADERS += i.to_bytes()
    else:
        ACCEPTABLE_MSG_HEADERS += h.to_bytes()

#Heater Constants
HEATERS = (0, 1) # Mapping for heater numbers
HEATER_RESISTANCE = (0.05, 0.06) #Ohms, (heater 0, heater 1), measured value, as different heaters are going to have different resistances
HEATER_SCALAR = (1, 1) #(heater 0, heater 1),heaters are going to have different thermal masses as bottom heater has more to heat up so having a scalar would allow both blocks to heat similarly
SUPPLY_VOLTAGE = 12 #Volts
time_start = time.time()

#Webhook Endpoints
TEST_SETTING_WEBHOOK_ENDPOINT = "http://localhost:3000/test-setting-update"
END_TEST_WEBHOOK_ENDPOINT = "http://localhost:3000/test-end"


class SerialComm(asyncio.Protocol):
    def __init__(self, power_queue:asyncio.Queue):
        """Class for managing serial communicaiton with the raspberry pi pico power distribution and control PCB
        Source for this method of using functools.partial: https://tinkering.xyz/async-serial/#the-rest
        Args:
            power_queue (asyncio.Queue): Queue instance that stores the data from the INA260 voltage and current monitoring
        """
        super().__init__()
        self.transport = None
        self.power_queue = power_queue
        self.duty_cycle = [0, 0] #% duty cycle of each heater, useful for ensuring that the power output lines up properly

    def connection_made(self, transport:serial_asyncio.SerialTransport):
        """Gets called when serial is connected, inherited function

        Args:
            transport (serial_asyncio.SerialTransport): input gets passed by erial_asyncio.create_serial_connection()
        """
        self.transport = transport
        self.pat = b'['+ACCEPTABLE_MSG_HEADERS+b'].{'+str(MSG_LEN-2).encode()+b'}'+TERMINATION.to_bytes()
        print(self.pat)
        self.read_buf = bytes()
        self.bytes_recv = 0
        self.msg = bytearray(MSG_LEN)
        print("SerialReader Connection Created")
        power_control_task = asyncio.ensure_future(self.power_control())
        power_control_task.set_name("Power-Control-Task")

    def connection_lost(self, exc:Exception):
        """Gets called when serial is disconnected/lost, inherited function

        Args:
            exc (Exception): Thrown exception
        """
        print(f"SerialReader Closed with exception: {exc}")
    async def parseMsg(self, msg:bytes):
        """Parse a message sent by the raspberry pi pico and add it the proper queue to get put into the database

        Args:
            msg (bytes): bytes object of length MSG_LEN that matched the self.pat
        """
        if msg[0] == INA260_DATA_HEADER[0]: #INA260 Data Heater 0
            mV = ((((msg[1]<<8)+msg[2])<<8)+msg[3])/100
            mA = ((((msg[4]<<8)+msg[5])<<8)+msg[6])/100
            print(f"Heater 0: {mV} mV | {mA} mA")
            await self.power_queue.put([0, mV, mA, self.duty_cycle[0], time.time()])

        elif msg[0] == INA260_DATA_HEADER[1]: #INA260 Data Heater 1
            mV = ((((msg[1]<<8)+msg[2])<<8)+msg[3])/100
            mA = ((((msg[4]<<8)+msg[5])<<8)+msg[6])/100
            print(f"Heater 1: {mV} mV | {mA} mA")
            await self.power_queue.put([1, mV, mA, self.duty_cycle[1], time.time()]) 
    
    def data_received(self, data):
        """add data sent over serial to the serial buffer and check for properly formatted messages using regex, then pass the message to parseMsg

        Args:
            data (bytes): _description_
        """
        # print("Reached Data Recieved")
        self.read_buf += data
        # print(self.read_buf)
        if len(self.read_buf)>= MSG_LEN:
            while True:
                match = re.search(self.pat, self.read_buf)
                if match == None:
                    break
                else:
                    asyncio.ensure_future(self.parseMsg(match.group(0)))
                    self.read_buf = self.read_buf[match.end():]
                    # print(self.read_buf)

    async def power_control(self):
        """Coroutine to infinitely loop and calculate the duty cycle of the heaters for the raspberry pi pico
        """
        try:
            while True:
                await asyncio.sleep(DUTY_CYCLE_UPDATE_PERIOD) #pause duty cycle update for a bit while being non-blocking
                curr_time = time.time()
                for heater in HEATERS:
                    self.duty_cycle[heater] = math.sqrt(HEATER_SCALAR[heater]*HEATER_RESISTANCE[heater]*(control_amplitude*math.sin(control_freq*(curr_time-time_start)/(2*math.pi))+control_amplitude))*100/SUPPLY_VOLTAGE
                
                self.sendDutyCycleMsg(2)
                print(f"Time: {curr_time-time_start} Heater 0: {self.duty_cycle[0]} Heater 1: {self.duty_cycle[1]}")

        except asyncio.CancelledError: #when .cancel() is called for this coroutine
            self.duty_cycle = [0, 0]
            self.sendDutyCycleMsg(2)
            await asyncio.sleep(1) #Wait for a while to ensure that the cancel message was sent before closing the serial port
            self.transport.close()
            print("Serial port closed and control task executed")
            

    def sendDutyCycleMsg(self, heater:int):
        """format the duty cycle info and send to raspberry pi pico

        Args:
            heater (int): 0: Heater 0 only, 1: Heater 1 only, 2: both heaters in the same message, 0 or 1 would only really be useful for thermal control
        """
        self.msg[0] = DUTY_CYCLE_CHANGE_HEADER[heater]
        if heater == 2: #Send duty cycle update to both heaters
            self.msg[1:4] = int(self.duty_cycle[0]*1000).to_bytes(3)
            self.msg[4:7] = int(self.duty_cycle[1]*1000).to_bytes(3)
        else:
            self.msg[1:4] = int(self.duty_cycle[heater]*1000).to_bytes(3)

        self.sendMsg()

    def sendMsg(self):
        """Add the data into the serial output buffer
        """
        self.transport.write(self.msg)


#AIOSQLITE
async def connectDatabase(db:str) -> aiosqlite.Connection:
    """ Connect to the sqlite database and initialize requires tables

    Args:
        db (str): database string, example: my_database.db

    Returns:
        aiosqlite.Connection: databse connection
    """
    database = await aiosqlite.connect(db)
    test_name = await database.execute_fetchone(f"SELECT id FROM {TEST_DIRECTORY_TABLE_NAME} ORDER BY time DESC LIMIT 1")
    test_name = test_name[0]

    #Set proper table names for this test
    global POWER_INITIALIZATION_QUERY, TEST_SETTING_INITIALIZATION_QUERY, TEST_SETTING_TABLE_NAME, TEST_SETTING_TABLE_NAME_BASE, POWER_TABLE_NAME, POWER_TABLE_NAME_BASE
    POWER_INITIALIZATION_QUERY = createPowerInitQuery(test_name)
    TEST_SETTING_INITIALIZATION_QUERY = createTestSettingInitQuery(test_name)
    TEST_SETTING_TABLE_NAME = testNameTableFormatter(TEST_SETTING_TABLE_NAME_BASE, test_name)
    POWER_TABLE_NAME = testNameTableFormatter(POWER_TABLE_NAME_BASE, test_name)

    #Create power table if it doesn't already exist
    await database.execute(POWER_INITIALIZATION_QUERY)
    #Create test_settings table if it doesn't already exist
    await database.execute(TEST_SETTING_INITIALIZATION_QUERY)

    return database

def testNameTableFormatter(table_name:str, test_name:str)-> str:
    """Returns the properly formatted table name string for all tables

    Args:
        table_name (str): Base name of the table, like test_settings
        test_name (str): name of the test

    Returns:
        str: table name for this specific test
    """
    return f"{table_name}_{test_name}"

def createPowerInitQuery(test_name:str)->str:
    """create the proper table creation query for the power data

    Args:
        test_name (str): name of the test

    Returns:
        str: proper query
    """
    ret = f'''
    CREATE TABLE IF NOT EXISTS {testNameTableFormatter(POWER_TABLE_NAME_BASE, test_name)} (
    heater_num REAL NOT NULL,
    mV REAL NOT NULL,
    mA REAL NOT NULL,
    duty_cycle REAL NOT NULL,
    time REAL NOT NULL
    )
    '''
    return ret

def createTestSettingInitQuery(test_name:str)->str:
    """create the proper table creation query for the test settings

    Args:
        test_name (str): name of the test

    Returns:
        str: proper query
    """
    ret = f'''
    CREATE TABLE IF NOT EXISTS {testNameTableFormatter(TEST_SETTING_TABLE_NAME_BASE, test_name)} (
    test_mode REAL NOT NULL,
    frequency REAL NOT NULL,
    amplitude REAL NOT NULL,
    time REAL NOT NULL
    )
    '''

async def powerQueueHandler(database:aiosqlite.Connection, power_table_name:str, powerqueue:asyncio.Queue):
    """Coroutine to infinietly loop and put INA260 data into the proper sqlite database table

    Args:
        database (aiosqlite.Connection):
        power_table_name (str): name of the table for power data inside primary sqlite database
        powerqueue (asyncio.Queue): queue that feeds all the INA260 data between coroutines
    """
    try:
        while True:
            pwr_data = await powerqueue.get()
            await database.execute(f"INSERT INTO {power_table_name} (heater_num, mV, mA, duty_cycle, time) VALUES ({pwr_data[0]}, {pwr_data[1]}, {pwr_data[2]}, {pwr_data[3]}, {pwr_data[4]})")
            await database.commit()
    except asyncio.CancelledError:
        print("Power Queue Shutting Down")

async def testSettingHookHandler(database:aiosqlite.Connection, test_setting_table:str):
    """handler for webhook pushed by website when user updates the test settings so the script checks the database 

    Args:
        database (aiosqlite.Connection):
        test_setting_table (str): name of the table for test setting data inside primary sqlite database
    """
    async with aiohttp.ClientSession() as session:
        while True:
            #Every time a new response is generated by the endpoint, this program updates its values based on the database, and then reconnects to the webhook waiting for the newone
            async with session.get(TEST_SETTING_WEBHOOK_ENDPOINT) as response:
                # http response should have the following format:
                # status: 200,
                # headers: { "content-type": "text/plain" },
                # body: "New Test Setting"
                if response.body == "New Test Setting": #If the response has the proper content
                    most_recent = await database.execute_fetchall(f"SELECT * FROM {test_setting_table} ORDER BY time DESC LIMIT 1") #Instead of using the webhook to transfer data about the new test settings, the database is used as the only groundtruth of information
                    most_recent = most_recent[0]
                    if most_recent != most_recent[0] or control_amplitude != most_recent[2] or control_modes_map[most_recent[0]] != control_mode: # check to see if there are any new values from the database so bad webhook messages are caught and the time isn't reset arbitrarily
                        most_recent = most_recent[0]
                        control_freq = most_recent[1] #Set new freq
                        control_amplitude = most_recent[2] #Set new amplitude
                        time_start = time.time() #Restart the time used by the sin wave calculator in SerialComm.powerControl
                        control_mode = control_modes_map[most_recent[0]] #Will throw key error if improper mode is 


async def webhookGracefulExit(loop:asyncio.AbstractEventLoop):
    """Wait for test over webhook to end this program

    Args:
        loop (asyncio.AbstractEventLoop): primary event loop
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(END_TEST_WEBHOOK_ENDPOINT) as response:
            # http response should have the following format:
            # status: 200,
            # headers: { "content-type": "text/plain" },
            # body: "Test Ended"
            if response.body == "New Test Setting": #If the response has the proper content
                await gracefulExit(loop)




def signalGracefulExit(*args):
    """function for signal handling, calls graceful exit when triggered.

    Args:
        stack_frame (frame object or none): see https://docs.python.org/3/library/signal.html#signal.signal 
        loop (asyncio.AbstractEventLoop): primary event loop
    """
    gracefulExit(loop)


def gracefulExit(loop:asyncio.AbstractEventLoop):
    """Gracefully exit whatevent loops can be gracefully exited, some, like the serial coroutine might not be so pleasant, based on https://www.roguelynn.com/words/asyncio-graceful-shutdowns/

    Args:
        loop (asyncio.AbstractEventLoop): primary event loop
    """
    graceful_exit_req_tasks = ["Power-Control-Task"] #Tasks that require a graceful exit, should be in order of exit priority
    print(asyncio.current_task())
    # tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    # print("Tasks at the beginning: ")
    # for t in tasks:
    #     print(t)

    #Ensure that task writing duty cycle data gets canceled first because otherwise the heaters could be left on
    serial_out_tasks = [t for t in asyncio.all_tasks() if t._coro.__name__ in graceful_exit_req_tasks]
    for t in serial_out_tasks:
        t.cancel()

    #Cancel the rest of the tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()

    

async def createMainCoroutines(loop:asyncio.AbstractEventLoop, serial_port:str, baud_rate:int, db:aiosqlite.Connection):
    """This function creates all the required coroutines to enable to use of run_until_complete to clean up exiting of the program

    Args:
        loop (asyncio.AbstractEventLoop): main event loop
        serial_port (str): serial port string
        baud_rate (int): boud rate of the serial port
        db (aiosqlite.Connection): primary data base for power and test setting data
    """
    power_queue = asyncio.Queue() #Power queue items should be a list with the following structure: (Heater Number, mV, mA, duty cycle, time)

    #initalize Serial Asyncio reader and writer
    serial_with_queue = partial(SerialComm, power_queue = power_queue)
    serial_coro = serial_asyncio.create_serial_connection(loop, serial_with_queue, port, baudrate=baud)
    serial_task = asyncio.ensure_future(serial_coro)
    serial_task.set_name("Serial-Comm-Task")
    print("SerialComm Scheduled")

    #Initialize powerQueueHandler coroutines
    power_queue_task = asyncio.ensure_future(powerQueueHandler(db, POWER_TABLE_NAME, power_queue))
    power_queue_task.set_name("Power-Queue-Task")
    print("powerQueueHandler Scheduled")

    #Initialize Webhook Coroutines
    webhook_exit_task = asyncio.ensure_future(webhookGracefulExit(loop)) #Monitor END_TEST_WEBHOOK_ENDPOINT to get shutdown signal from webserver
    webhook_exit_task.set_name("Webhook-Exit-Task")
    test_setting_task = asyncio.ensure_future(testSettingHookHandler(db, TEST_SETTING_TABLE_NAME))
    test_setting_task.set_name("Test-Settting-Handler-Task")
    
    try:
        # await asyncio.gather(serial_task, power_queue_task)
        await asyncio.gather(serial_task, power_queue_task, webhook_exit_task, test_setting_task)
    except asyncio.CancelledError:
        print("createMainCoroutines Cancelled")        


if __name__ == "__main__":
    # Argument parsing for serial port
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=None)
    parser.add_argument("--baud", default=115200)
    parser.add_argument("--database", default='your_database.db')
    args = parser.parse_args()
    port = args.port
    baud = args.baud
    database = args.database

    # If no port is given, use Serial_Helper to choose one
    if port is None:
        port = Serial_Helper.terminalChooseSerialDevice()
    #If port given doesn't exist, use Serial_Helper
    elif Serial_Helper.checkValidSerialDevice(port) is False:
        Serial_Helper.terminalChooseSerialDevice()

    # Separate loop required to properly initialize the database before moving on to the rest of the code.
    loop = asyncio.get_event_loop()
    db = asyncio.ensure_future(connectDatabase(database))
    loop.run_until_complete(db)
    db = db.result()

    # New eventloop that runs forever to handle the bulk of this script
    loop = asyncio.get_event_loop()

    #Add signal handler tasks
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        signal.signal(s, signalGracefulExit)
    
    create_main_task = asyncio.ensure_future(createMainCoroutines(loop, port, baud, db))
    
    loop.run_until_complete(create_main_task)
    print("Exited Loop")
    loop.close()
    os._exit(1)
