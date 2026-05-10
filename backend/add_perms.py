import sqlite3
import json
conn = sqlite3.connect('backend/distress_engine.db')
c = conn.cursor()
try:
    c.execute("ALTER TABLE users ADD COLUMN permissions JSON DEFAULT '[]'")
except Exception as e:
    print(e)

c.execute("UPDATE users SET permissions = ? WHERE role = ?", (json.dumps(['can_manage_leaves', 'can_manage_users', 'can_view_grades']), 'admin'))
c.execute("UPDATE users SET permissions = ? WHERE role = ?", (json.dumps(['can_manage_leaves']), 'teacher'))
conn.commit()
conn.close()
print("Added permissions successfully")
