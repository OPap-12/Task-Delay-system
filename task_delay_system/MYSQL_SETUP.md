# MySQL Setup Guide for Task Management System

## 📋 Understanding MySQL Workbench vs mysqlclient

### **MySQL Workbench** (GUI Tool)
- **What it is:** A visual database management tool (like a visual editor)
- **Purpose:** To view, edit, and manage your MySQL databases visually
- **Do you need it?** Optional - it's just a tool to see your data visually
- **Download:** https://dev.mysql.com/downloads/workbench/

### **mysqlclient** (Python Package)
- **What it is:** A Python library that allows Django to connect to MySQL
- **Purpose:** Required for Django to communicate with MySQL database
- **Do you need it?** YES - if you want to use MySQL instead of SQLite
- **Installation:** See below

---

## 🔧 Step-by-Step MySQL Setup

### **Step 1: Install MySQL Server**

1. Download MySQL Server from: https://dev.mysql.com/downloads/mysql/
2. Install MySQL Server (choose "Developer Default" or "Server only")
3. During installation, remember your root password
4. Make sure MySQL service is running (check Windows Services)

### **Step 2: Create Database in MySQL**

**Option A: Using MySQL Workbench (Visual Method)**
1. Open MySQL Workbench
2. Connect to your MySQL server (usually localhost, port 3306)
3. Click "Create a new schema" (database icon)
4. Name it: `task_management_db`
5. Click "Apply"

**Option B: Using Command Line**
```bash
mysql -u root -p
```
Then type:
```sql
CREATE DATABASE task_management_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### **Step 3: Install mysqlclient (Python Package)**

**For Windows (Recommended Method):**

1. **Download pre-built wheel file:**
   - Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient
   - Download the file matching your Python version:
     - Example: `mysqlclient‑2.2.0‑cp39‑cp39‑win_amd64.whl` (for Python 3.9, 64-bit)
     - Check your Python version: `python --version`

2. **Install the wheel file:**
   ```bash
   cd "C:\Users\Arpit\OneDrive\Desktop\Task_Delay_System - Copy"
   .\venv\Scripts\Activate.ps1
   pip install path\to\downloaded\mysqlclient‑2.2.0‑cp39‑cp39‑win_amd64.whl
   ```

**Alternative: Install using pip (may require Visual C++ Build Tools)**
```bash
pip install mysqlclient
```

**If mysqlclient installation fails, try PyMySQL instead:**
```bash
pip install pymysql
```

Then add this to your `task_delay_system/task_delay_system/__init__.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### **Step 4: Update Django Settings**

1. Open `task_delay_system/task_delay_system/settings.py`
2. Find the `DATABASES` section
3. Comment out the SQLite configuration
4. Uncomment and update the MySQL configuration:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'task_management_db',  # Your database name
        'USER': 'root',  # Your MySQL username
        'PASSWORD': 'your_mysql_password',  # Your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

### **Step 5: Run Migrations**

```bash
cd task_delay_system
python manage.py migrate
```

This will create all the tables in your MySQL database.

### **Step 6: Create Superuser (if needed)**

```bash
python manage.py createsuperuser
```

---

## ✅ Verification

### **Check if MySQL Connection Works:**

```bash
python manage.py dbshell
```

If you see MySQL prompt, it's working!

### **View Database in MySQL Workbench:**

1. Open MySQL Workbench
2. Connect to your server
3. Expand "Schemas" → `task_management_db`
4. You should see tables: `tasks_task`, `django_migrations`, etc.

---

## 🔄 Switching Back to SQLite

If you want to switch back to SQLite:

1. Comment out MySQL configuration
2. Uncomment SQLite configuration in `settings.py`
3. Run migrations: `python manage.py migrate`

---

## 🐛 Troubleshooting

### **Error: "No module named 'mysqlclient'"**
- Install mysqlclient: `pip install mysqlclient`
- Or use PyMySQL alternative (see Step 3)

### **Error: "Can't connect to MySQL server"**
- Make sure MySQL service is running
- Check if MySQL is running on port 3306
- Verify username/password in settings.py

### **Error: "Access denied for user"**
- Check MySQL username and password
- Make sure the user has privileges on the database

### **Error: "Unknown database 'task_management_db'"**
- Create the database first (see Step 2)
- Or change the database name in settings.py to an existing one

---

## 📝 Summary

- **MySQL Workbench:** Optional GUI tool (like a visual editor for databases)
- **mysqlclient:** Required Python package (allows Django to connect to MySQL)
- **You need BOTH:** MySQL Server + mysqlclient package
- **MySQL Workbench is optional** - you can manage databases via command line too

---

**Current Status:** Your app is using SQLite (works fine for development)
**To Switch to MySQL:** Follow the steps above
