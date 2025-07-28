import sqlite3
import os
from datetime import datetime,timezone,timedelta

DB_PATH = os.path.join("database", "sensor_backup.db")

# 폴더 생성
os.makedirs("database", exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_backup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_serial TEXT NOT NULL,
            receiver_serial TEXT,
            timestamp TEXT NOT NULL,
            obj_temp REAL,
            die_temp REAL,
            roll REAL,
            pitch REAL,
            tilt REAL,
            current REAL,
            is_synced INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def migrate_add_receiver_serial():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE sensor_backup ADD COLUMN receiver_serial TEXT")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise
    conn.close()

def insert_sensor_data(sender_serial, receiver_serial, obj_temp, die_temp, roll, pitch, tilt, current, is_synced):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    kst_now = datetime.utcnow() + timedelta(hours=9)
    timestamp = kst_now.replace(tzinfo=timezone(timedelta(hours=9))).isoformat()

    cursor.execute('''
        INSERT INTO sensor_backup (
            sender_serial, receiver_serial, timestamp, obj_temp, die_temp,
            roll, pitch, tilt, current, is_synced
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (sender_serial, receiver_serial, timestamp, obj_temp, die_temp, roll, pitch, tilt, current, is_synced))

    conn.commit()
    conn.close()

def mark_data_as_synced(record_ids):
    if not record_ids:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executemany('''
        UPDATE sensor_backup SET is_synced = 1 WHERE id = ?
    ''', [(rid,) for rid in record_ids])
    conn.commit()
    conn.close()

def get_all_sender_serials():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT sender_serial FROM sensor_backup')
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def get_sensor_data_by_serial(sender_serial):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, receiver_serial, obj_temp, die_temp, roll, pitch, tilt, current, is_synced
        FROM sensor_backup
        WHERE sender_serial = ?
        ORDER BY timestamp DESC
    ''', (sender_serial,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_unsynced_data(limit=100):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, sender_serial, receiver_serial, timestamp, obj_temp, die_temp, roll, pitch, tilt, current
        FROM sensor_backup
        WHERE is_synced = 0
        ORDER BY timestamp ASC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows