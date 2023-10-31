import sqlite3

conn = sqlite3.connect('your_database.db')
cursor = conn.cursor()

# List all table names in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Drop each table
for table in tables:
    cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")

# Commit and close
conn.commit()
cursor.close()
conn.close()
