# Task Management System - Testing Guide

## 🚀 Quick Start

The Django development server is now running! You can access the application using the URLs below.

---

## 📍 **Access URLs**

### **Main Application (User Interface)**
- **URL:** http://127.0.0.1:8000/
- **OR:** http://localhost:8000/
- **Description:** This is the main task management interface where you can:
  - View all tasks
  - Create new tasks
  - Update existing tasks
  - Delete tasks
  - Mark tasks as complete/pending
  - Filter tasks by status (All, Pending, Completed, At Risk, Delayed)

### **Django Admin Panel**
- **URL:** http://127.0.0.1:8000/admin/
- **OR:** http://localhost:8000/admin/
- **Description:** Administrative interface for managing tasks and users

---

## 🔐 **Admin Login Credentials**

You already have a superuser account created. To find out your username or create a new one:

### **Option 1: Check Existing Superuser**
Run this command in your terminal:
```bash
cd task_delay_system
python manage.py shell
```
Then in the shell:
```python
from django.contrib.auth import get_user_model
User = get_user_model()
for user in User.objects.filter(is_superuser=True):
    print(f"Username: {user.username}, Email: {user.email}")
```

### **Option 2: Create a New Superuser**
If you forgot your password or want to create a new admin account:
```bash
cd task_delay_system
python manage.py createsuperuser
```
Follow the prompts to enter:
- Username
- Email (optional)
- Password

---

## 🧪 **Testing Steps**

### **1. Test Main Application (User Interface)**

1. Open your browser and go to: **http://127.0.0.1:8000/**
2. You should see the Task Management System homepage
3. Click **"+ Add New Task"** to create your first task
4. Fill in the form:
   - Task Title (required)
   - Description (optional)
   - Due Date (required - use the date picker)
5. Click **"Create Task"**
6. Test the following features:
   - ✅ **View Tasks:** See all your tasks in card format
   - ✅ **Filter Tasks:** Use the filter buttons (All, Pending, Completed, At Risk, Delayed)
   - ✅ **Edit Task:** Click "Edit" button on any task
   - ✅ **Mark Complete:** Click "Mark Complete" button
   - ✅ **Delete Task:** Click "Delete" button (confirmation required)
   - ✅ **Toggle Status:** Use "Mark Complete" / "Mark Pending" to toggle

### **2. Test Admin Panel**

1. Open your browser and go to: **http://127.0.0.1:8000/admin/**
2. Login with your superuser credentials
3. You should see:
   - **Tasks** section - Manage all tasks
   - **Users** section - Manage user accounts
   - **Groups** section - Manage user groups
4. Click on **"Tasks"** to see all tasks with:
   - List view with filters
   - Search functionality
   - Ability to edit/delete tasks
   - Better organization with date hierarchy

---

## 🛠️ **Common Commands**

### **Start the Server**
```bash
cd task_delay_system
python manage.py runserver
```

### **Stop the Server**
Press `Ctrl + C` in the terminal where the server is running

### **Run on Different Port**
```bash
python manage.py runserver 8080
```
Then access at: http://127.0.0.1:8080/

### **Run on Network (Accessible from other devices)**
```bash
python manage.py runserver 0.0.0.0:8000
```
Then access from other devices using your computer's IP address: http://YOUR_IP:8000/

### **Create Superuser**
```bash
python manage.py createsuperuser
```

### **Run Migrations (if needed)**
```bash
python manage.py makemigrations
python manage.py migrate
```

### **Access Django Shell**
```bash
python manage.py shell
```

---

## 📱 **Access from Other Devices (Same Network)**

If you want to access the application from your phone or another computer:

1. Find your computer's IP address:
   - **Windows:** Open Command Prompt and type `ipconfig`
   - Look for "IPv4 Address" (usually something like 192.168.x.x)

2. Start the server with:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

3. Access from other device:
   - **URL:** http://YOUR_IP_ADDRESS:8000/
   - **Example:** http://192.168.1.100:8000/

---

## ✅ **Features to Test**

- [x] Create new tasks
- [x] View all tasks
- [x] Edit existing tasks
- [x] Delete tasks
- [x] Mark tasks as complete
- [x] Mark tasks as pending
- [x] Filter by status (Pending/Completed)
- [x] Filter by delay status (At Risk/Delayed)
- [x] View task details (title, description, due date, status)
- [x] See delayed tasks (completed after due date)
- [x] See at-risk tasks (due within 2 days)
- [x] Admin panel access
- [x] Responsive design (test on mobile/tablet)

---

## 🐛 **Troubleshooting**

### **Server won't start**
- Make sure virtual environment is activated: `.\venv\Scripts\Activate.ps1`
- Check if port 8000 is already in use
- Try a different port: `python manage.py runserver 8080`

### **Can't access admin panel**
- Make sure you have a superuser account
- Create one: `python manage.py createsuperuser`
- Check if you're using the correct URL: http://127.0.0.1:8000/admin/

### **Static files (CSS) not loading**
- Make sure `STATICFILES_DIRS` is set in `settings.py` (already configured)
- Run: `python manage.py collectstatic` (if needed)

### **Database errors**
- Run migrations: `python manage.py migrate`
- Check if `db.sqlite3` exists in the `task_delay_system` folder

---

## 📝 **Sample Test Data**

You can create test tasks with different scenarios:
1. **Task due today** - Should show as "At Risk"
2. **Task due tomorrow** - Should show as "At Risk"
3. **Task due next week** - Should show as normal
4. **Overdue task** - Should show as "Delayed" if completed late
5. **Completed task** - Should show completion status

---

**Happy Testing! 🎉**
