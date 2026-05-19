import sqlite3
import os

db_path = 'distress_engine.db'
if not os.path.exists(db_path):
    print('DB not found at', db_path)
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, email, role FROM users WHERE email='admin@yagel-yaakov.edu'")
    user = c.fetchone()
    if user:
        print('User found:', user)
    else:
        print('Admin user not found in DB.')
        
    c.execute("SELECT email, role FROM users")
    print("All users:", c.fetchall())
