import sqlite3

conn = sqlite3.connect("database/sensor_backup.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM sensor_backup ORDER BY timestamp DESC LIMIT 10")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
