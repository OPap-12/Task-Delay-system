# MySQL Database Connection Guide

## ✅ **Step 1: Create Database in MySQL**

### **Using MySQL Workbench (Visual Method):**

1. **Open MySQL Workbench**
2. **Connect to your MySQL server:**
   - Click on your connection (usually "Local instance MySQL" or similar)
   - Enter your root password if prompted
3. **Create the database:**
   - Click the "Create a new schema" icon (database icon with +)
   - Or right-click in Schemas panel → "Create Schema"
   - **Database name:** `task_management_db`
   - **Collation:** `utf8mb4_unicode_ci` (or default)
   - Click **"Apply"**

### **Using Command Line:**

1. **Open Command Prompt or MySQL Command Line Client**
2. **Login to MySQL:**
   ```bash
   mysql -u root -p
   ```
   (Enter your MySQL root password when prompted)

3. **Create database:**
   ```sql
   CREATE DATABASE task_management_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   EXIT;
   ```

---

## ✅ **Step 2: Update settings.py**

The `settings.py` file has been updated with MySQL configuration. You need to:

1. **Open:** `task_delay_system/task_delay_system/settings.py`
2. **Find the DATABASES section** (around line 76)
3. **Update these values:**
   ```python
   DATABASES = {
       'default': {
           # Recommended on Windows/Python 3.14 (no compilation needed):
           'ENGINE': 'mysql.connector.django',
           'NAME': 'task_management_db',  # Your database name
           'USER': 'root',  # Your MySQL username
           'PASSWORD': 'your_password',  # Your MySQL password (if you have one)
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

Also make sure you installed the driver:

```bash
python -m pip install mysql-connector-python
```

**Important:** 
- If your MySQL has **no password**, leave `'PASSWORD': ''` (empty string)
- If your MySQL has a **password**, enter it: `'PASSWORD': 'your_password'`

---

## ✅ **Step 3: Run Migrations**

After updating settings.py, run migrations to create tables:

```bash
cd task_delay_system
python manage.py migrate
```

This will create all the necessary tables in your MySQL database.

---

## 📊 **Step 4: View Database in MySQL Workbench**

### **Where to See Your Database:**

1. **Open MySQL Workbench**
2. **Connect to your MySQL server** (click on your connection)
3. **In the left sidebar (Schemas panel):**
   - Expand **"Schemas"**
   - You should see **`task_management_db`** database
   - Click on it to expand

4. **View Tables:**
   - Expand **`task_management_db`**
   - Click on **"Tables"**
   - You'll see all your Django tables:
     - `auth_user` - User accounts
     - `auth_group` - User groups
     - `tasks_task` - Your tasks
     - `django_migrations` - Migration history
     - And more...

5. **View Data:**
   - Right-click on any table (e.g., `tasks_task`)
   - Select **"Select Rows - Limit 1000"**
   - You'll see all the data in that table

### **Quick Data View:**

1. **Double-click on a table** (e.g., `tasks_task`)
2. **Click the "Table Data" tab** at the bottom
3. **You'll see all records** in a spreadsheet-like view

---

## 🔍 **What Tables You'll See:**

### **Main Tables:**

1. **`tasks_task`** - All your tasks
   - Columns: `id`, `user_id`, `title`, `description`, `due_date`, `created_at`, `completed`, `completed_at`, `priority`

2. **`auth_user`** - All registered users
   - Columns: `id`, `username`, `email`, `password`, `first_name`, `last_name`, `is_staff`, `is_superuser`, etc.

3. **`django_migrations`** - Migration history
   - Tracks which migrations have been applied

4. **`django_session`** - User sessions
   - Active user login sessions

### **Other Django Tables:**
- `auth_group` - User groups
- `auth_permission` - Permissions
- `django_content_type` - Content types
- `django_admin_log` - Admin action logs

---

## 🧪 **Test the Connection:**

### **Method 1: Django Shell**
```bash
python manage.py shell
```
Then type:
```python
from tasks.models import Task
Task.objects.all()
```
If it works, your connection is good!

### **Method 2: Django dbshell**
```bash
python manage.py dbshell
```
This opens MySQL command line. Type:
```sql
SHOW TABLES;
USE task_management_db;
SELECT * FROM tasks_task;
```

---

## 🐛 **Troubleshooting**

### **Error: "Can't connect to MySQL server"**
- Make sure MySQL server is running
- Check if MySQL is running on port 3306
- Verify HOST is 'localhost' or '127.0.0.1'

### **Error: "Access denied for user"**
- Check your MySQL username and password in settings.py
- Make sure the user has privileges on the database

### **Error: "Unknown database 'task_management_db'"**
- Create the database first (see Step 1)
- Or change the database name in settings.py to an existing one

### **Error: "No module named 'mysql.connector'"**
- Install the MySQL Connector/Python driver:
  ```bash
  python -m pip install mysql-connector-python
  ```

### **Can't see tables in MySQL Workbench**
- Make sure you ran migrations: `python manage.py migrate`
- Refresh the Schemas panel in MySQL Workbench (right-click → Refresh All)

---

## 📝 **Quick Reference**

### **Access URLs:**
- **Register:** http://127.0.0.1:8000/register/
- **Login:** http://127.0.0.1:8000/login/
- **Logout:** http://127.0.0.1:8000/logout/ (or click Logout button)

### **Database Location:**
- **MySQL Workbench:** Open → Connect → Schemas → `task_management_db` → Tables

### **View Data:**
- Right-click table → "Select Rows - Limit 1000"
- Or double-click table → "Table Data" tab

---

## ✅ **Summary**

1. ✅ Create database `task_management_db` in MySQL Workbench
2. ✅ Update `settings.py` with your MySQL password
3. ✅ Run `python manage.py migrate`
4. ✅ View database in MySQL Workbench under Schemas → `task_management_db` → Tables

**Your database is now connected and you can see all your data in MySQL Workbench!** 🎉
