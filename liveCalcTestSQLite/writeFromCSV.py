import sqlite3
import pandas as pd
import utils as ut
import time

VALUES_TO_READ = 22000
SLEEP_TIME = 1

# Connect to the database
conn = sqlite3.connect('your_database.db')

# Create a cursor
cursor = conn.cursor()

directory = "fully_converted_AlStrip_TC34_10msSampling_MountedTCs_L=0.71cm_TIMpaste_24VCPUFan_f=0.001.plw_1.csv"

# Read the original CSV file
df = pd.read_csv(directory)
df = ut.clean_dataframe(df)

# create lists to store data

date_times = list(df['Date/Time'])
times1 = [i * 0.01 for i in range(len(df))]
temps1 = list(df['TC3'])
temps2 = list(df['TC4'])
temps5 = list(df['TC5'])
temps6 = list(df['TC6'])

# Create a table
cursor.execute('''CREATE TABLE IF NOT EXISTS Data1 (
                date_time TEXT NOT NULL,
                relTime REAL NOT NULL,
                temp1 REAL NOT NULL,
                temp2 REAL NOT NULL,
                temp5 REAL,
                temp6 REAL,
                power REAL)''')

for i in range(0, len(temps1), VALUES_TO_READ):
    time.sleep(SLEEP_TIME)

    # Add data
    date_time = date_times[i:i + VALUES_TO_READ]
    time1 = times1[i:i + VALUES_TO_READ]
    temp1 = temps1[i:i + VALUES_TO_READ]
    temp2 = temps2[i:i + VALUES_TO_READ]

    data_to_insert = list(zip(date_time, time1, temp1, temp2))

    cursor.executemany("INSERT INTO Data1 (date_time, relTime, temp1, temp2) VALUES (?, ?, ?, ?)",
                       data_to_insert)

    # Commit the changes to the database
    conn.commit()

# Close the cursor and the connection
cursor.close()
conn.close()