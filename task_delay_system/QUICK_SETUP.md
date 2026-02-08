# Quick Setup Guide - Register, Login & MySQL

## ✅ **Register and Login ARE Already Added!**

### **Access URLs:**
- **Register:** http://127.0.0.1:8000/register/
- **Login:** http://127.0.0.1:8000/login/
- **Logout:** Click "Logout" button when logged in

---

## 🗄️ **MySQL Database Setup**

### **Step 1: Create Database in MySQL Workbench**

1. Open **MySQL Workbench**
2. Connect to your MySQL server (enter root password)
3. Click **"Create a new schema"** (database icon with +)
4. **Name:** `task_management_db`
5. Click **"Apply"**

### **Step 2: Update settings.py**

Open `task_delay_system/task_delay_system/settings.py` and find the DATABASES section (around line 76).

**If your MySQL has NO password:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'task_management_db',
        'USER': 'root',
        'PASSWORD': '',  # Empty if no password
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
```

**If your MySQL HAS a password:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'task_management_db',
        'USER': 'root',
        'PASSWORD': 'your_password_here',  # Enter your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
```

### **Step 3: Run Migrations**

```bash
cd task_delay_system
python manage.py migrate
```

This creates all tables in your MySQL database.

---

## 📊 **Where to See Your Database**

### **In MySQL Workbench:**

1. **Open MySQL Workbench**
2. **Connect to your MySQL server**
3. **In the left sidebar (Schemas panel):**
   - Expand **"Schemas"**
   - Find **`task_management_db`**
   - Expand it
   - Click on **"Tables"**

4. **You'll see these tables:**
   - `tasks_task` - All your tasks
   - `auth_user` - All registered users
   - `django_migrations` - Migration history
   - And more...

5. **To view data:**
   - Right-click on a table (e.g., `tasks_task`)
   - Select **"Select Rows - Limit 1000"**
   - Or double-click the table → "Table Data" tab

---

## 🚀 **Quick Start**

1. **Create database** in MySQL Workbench: `task_management_db`
2. **Update settings.py** with your MySQL password (or leave empty)
3. **Run migrations:** `python manage.py migrate`
4. **Start server:** `python manage.py runserver`
5. **Access:**
   - Register: http://127.0.0.1:8000/register/
   - Login: http://127.0.0.1:8000/login/
6. **View database:** MySQL Workbench → Schemas → `task_management_db` → Tables

---

## 🐛 **If MySQL Connection Fails**

### **Option 1: Use SQLite (Temporary)**
If MySQL isn't working, you can temporarily use SQLite:

In `settings.py`, comment out MySQL and uncomment SQLite:
```python
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         ...
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### **Option 2: Fix MySQL Connection**
- Make sure MySQL server is running
- Check your password in settings.py
- Verify database `task_management_db` exists
- Check if PyMySQL is installed: `pip install pymysql`

---

**Everything is ready! Just follow the steps above.** 🎉
