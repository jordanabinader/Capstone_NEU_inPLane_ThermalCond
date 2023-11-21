import csv
import sqlite3

# Connect to the database
conn = sqlite3.connect('your_database.db')

# Create a cursor
cursor = conn.cursor()

# Execute a query to fetch all data from the table
cursor.execute("SELECT * FROM TestData1SEP")

# Fetch all rows
rows = cursor.fetchall()

# Define the CSV file path
csv_file_path = 'table_dataSEP.csv'

# Write the data to a CSV file
with open(csv_file_path, 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)

    # Write the header
    header = [description[0] for description in cursor.description]
    csv_writer.writerow(header)

    # Write the rows
    csv_writer.writerows(rows)

print(f"Data exported to {csv_file_path}")

# Close the cursor and the connection
cursor.close()
conn.close()
