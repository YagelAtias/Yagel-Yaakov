# Database Management Guide - Yagel-Yaakov Project

## 📍 Database Location
Your SQLite database is located at:
```
C:\Users\yagel\Desktop\Coding\Python programming\Yagel-Yaakov\backend\distress_engine.db
```

## 🛠️ Tools to Manage Your Database

### Option 1: DB Browser for SQLite (Recommended - GUI Tool)
**Download:** https://sqlitebrowser.org/dl/

**How to use:**
1. Download and install DB Browser for SQLite
2. Open the application
3. Click "Open Database"
4. Navigate to and open: `C:\Users\yagel\Desktop\Coding\Python programming\Yagel-Yaakov\backend\distress_engine.db`
5. You'll see all your tables on the left sidebar

**Features:**
- ✅ Browse data in tables (click "Browse Data" tab)
- ✅ Execute SQL queries (click "Execute SQL" tab)
- ✅ Edit data directly by double-clicking cells
- ✅ Add new rows by clicking "Insert Record"
- ✅ Delete rows by right-clicking
- ✅ Export/Import data

### Option 2: VS Code Extension (If you use VS Code)
1. Install extension: "SQLite Viewer" by Florian Klampfer
2. Right-click on `distress_engine.db` in VS Code
3. Select "Open Database"

### Option 3: Command Line (Python)
Create a file called `db_manager.py` in your backend folder:

```python
import sqlite3
from datetime import datetime

# Connect to database
db_path = "distress_engine.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Helper function to view all records from a table
def view_table(table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

# Helper function to add a test student
def add_test_student():
    cursor.execute("""
        INSERT INTO students (first_name, last_name, email, hashed_password,
                            grade_level, organization_id, classroom_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("Test", "Student", "test@yy.edu", "hashed_pass", "Grade 10", 1, 1))
    conn.commit()
    print("Test student added!")

# Example: View all courses
print("=== All Courses ===")
view_table("courses")

# Example: View all users
print("\n=== All Users ===")
view_table("users")

# Close connection
conn.close()
```

Run it with: `python db_manager.py`

---

## 📊 Common Database Operations

### 1. View All Courses
```sql
SELECT * FROM courses;
```

### 2. View All Users (Teachers/Staff)
```sql
SELECT id, full_name, email, role FROM users;
```

### 3. View All Students
```sql
SELECT * FROM students;
```

### 4. Add a Test Teacher
```sql
INSERT INTO users (email, full_name, hashed_password, role, organization_id)
VALUES ('teacher@yy.edu', 'מורה בדיקה', '$2b$12$hashedpassword', 'teacher', 1);
```

### 5. Add a Test Student
```sql
INSERT INTO students (first_name, last_name, email, hashed_password, grade_level, organization_id, classroom_id)
VALUES ('דני', 'כהן', 'danny@yy.edu', '$2b$12$hashedpassword', 'כיתה י', 1, 1);
```

### 6. Assign a Teacher to a Course
```sql
UPDATE courses
SET teacher_id = 1  -- Replace with actual teacher ID
WHERE id = 1;  -- Replace with actual course ID
```

### 7. Assign Students to a Course
```sql
INSERT INTO student_courses (student_id, course_id)
VALUES (1, 1),  -- Student 1 to Course 1
       (2, 1),  -- Student 2 to Course 1
       (3, 1);  -- Student 3 to Course 1
```

### 8. View Course with Teacher Name
```sql
SELECT c.id, c.name, u.full_name as teacher_name
FROM courses c
LEFT JOIN users u ON c.teacher_id = u.id;
```

### 9. View Students in a Course
```sql
SELECT s.id, s.first_name, s.last_name, s.grade_level
FROM students s
JOIN student_courses sc ON s.id = sc.student_id
WHERE sc.course_id = 1;  -- Replace with your course ID
```

### 10. View All Exams for a Course
```sql
SELECT * FROM exams WHERE course_id = 1;  -- Replace with your course ID
```

---

## 🧪 Quick Test Data Setup

Copy and paste this SQL script in DB Browser (Execute SQL tab) to create test data:

```sql
-- Add test students (if you don't have any)
INSERT INTO students (first_name, last_name, email, hashed_password, grade_level, organization_id, classroom_id)
VALUES
('יוסי', 'לוי', 'yossi@yy.edu', '$2b$12$test', 'כיתה י', 1, 1),
('שרה', 'כהן', 'sarah@yy.edu', '$2b$12$test', 'כיתה י', 1, 1),
('דוד', 'מזרחי', 'david@yy.edu', '$2b$12$test', 'כיתה יא', 1, 1);

-- Get the IDs of the students we just created
-- Run this to see their IDs:
SELECT id, first_name, last_name FROM students;

-- Assign students to your course (replace course_id and student IDs)
INSERT INTO student_courses (student_id, course_id)
VALUES
(1, 1),  -- Replace first number with actual student ID
(2, 1),  -- Replace first number with actual student ID
(3, 1);  -- Replace first number with actual student ID

-- Add a test exam
INSERT INTO exams (course_id, subject, date_scheduled, description)
VALUES (1, 'מבחן אמצע - אלגברה', '2026-06-15 10:00:00', 'מבחן על פרקים 1-3');
```

---

## 🔍 Finding Your User ID (יגל אטיאס)

Run this query to find your user ID:
```sql
SELECT id, full_name, email, role FROM users WHERE email LIKE '%yagel%' OR full_name LIKE '%יגל%';
```

---

## 💡 Tips

1. **Always backup before making changes:**
   - Copy `distress_engine.db` to `distress_engine_backup.db` before experimenting

2. **Use transactions in DB Browser:**
   - Click "Begin Transaction" before making changes
   - Click "Commit" if everything looks good
   - Click "Rollback" to undo if something went wrong

3. **Foreign Key Constraints:**
   - When adding students to courses, make sure both the student_id and course_id exist
   - When setting teacher_id on a course, make sure that user ID exists

4. **Password Hashes:**
   - For testing, you can use dummy hash: `$2b$12$test`
   - Real passwords need proper bcrypt hashing (done automatically through the API)

---

## 🚀 Quick Commands Cheat Sheet

| Task | SQL Command |
|------|-------------|
| View all tables | `.tables` (in sqlite3 CLI) |
| View table structure | `PRAGMA table_info(table_name);` |
| Count records | `SELECT COUNT(*) FROM table_name;` |
| Delete all from table | `DELETE FROM table_name;` |
| Reset auto-increment | `DELETE FROM sqlite_sequence WHERE name='table_name';` |

---

## ⚠️ Important Notes

- The `encrypted_dek` field in users table is for encryption keys - you can use a dummy value for testing
- The `organization_id` should be 1 for all your test data (assuming single organization)
- When creating courses, make sure the `teacher_id` points to a valid user with role 'teacher', 'counselor', or 'admin'
- Student passwords in the database are hashed - you won't see the actual passwords

---

## 🎯 Example: Complete Setup for Testing Your Course

```sql
-- 1. Find your user ID
SELECT id, full_name FROM users WHERE full_name LIKE '%יגל%';
-- Let's say your ID is 1

-- 2. Create a course and assign yourself as teacher
INSERT INTO courses (name, organization_id, teacher_id)
VALUES ('מתמטיקה 4 יח״ל - קבוצה א', 1, 1);  -- Replace 1 with your actual user ID

-- 3. Get the course ID that was just created
SELECT id, name FROM courses ORDER BY id DESC LIMIT 1;
-- Let's say the course ID is 1

-- 4. Assign students to this course (make sure these student IDs exist)
INSERT INTO student_courses (student_id, course_id)
SELECT id, 1 FROM students LIMIT 3;  -- Assigns first 3 students to course 1

-- 5. Add an exam
INSERT INTO exams (course_id, subject, date_scheduled, description)
VALUES (1, 'מבחן חצי שנתי', '2026-06-20 09:00:00', 'חומר פרקים 1-5');

-- 6. Verify everything
SELECT 'Course' as type, name as info FROM courses WHERE id = 1
UNION ALL
SELECT 'Students', COUNT(*) FROM student_courses WHERE course_id = 1
UNION ALL
SELECT 'Exams', COUNT(*) FROM exams WHERE course_id = 1;
```

---

Need help? Just ask! 😊
