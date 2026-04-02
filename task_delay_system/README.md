# Task Delay System

A Django-based task management system with delay prediction, risk scoring, and analytics.

## Features

- **User Authentication** — Registration, login/logout with CSRF protection
- **Task Management** — Full CRUD (Create, Read, Update, Delete) with per-user ownership
- **Priority System** — Low, Medium, High priority for each task
- **Delay Prediction** — Estimates likelihood of task delay based on due date proximity
- **Risk Scoring** — 0–100 risk score combining due date and priority factors
- **Analytics Dashboard** — Aggregated statistics, at-risk tasks, high-risk alerts
- **Pagination** — Paginated task list (10 per page)
- **Filtering** — Filter by status (Pending/Completed) and delay state (At Risk/Delayed)

## Tech Stack

- **Backend:** Django 4.2
- **Database:** SQLite (default) / MySQL (configurable)
- **Auth:** Django built-in authentication
- **Styling:** Custom CSS

## Quick Start

### 1. Clone & Create Virtual Environment

```bash
git clone <repo-url>
cd task_delay_system
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the template and edit with your values:

```bash
cp .env.example .env
```

Key settings in `.env`:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | *(required)* |
| `DEBUG` | Debug mode | `True` |
| `DB_ENGINE` | `sqlite` or `mysql` | `sqlite` |
| `DB_NAME` | MySQL database name | `task_management_db` |
| `DB_USER` | MySQL user | `root` |
| `DB_PASSWORD` | MySQL password | *(required if mysql)* |

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Start Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — register an account to start managing tasks.

## Running Tests

```bash
python manage.py test tasks -v2
```

## Project Structure

```
task_delay_system/
├── task_delay_system/       # Project settings & root URL config
│   ├── settings.py          # Env-based configuration via python-decouple
│   ├── urls.py
│   └── wsgi.py
├── tasks/                   # Main application
│   ├── models.py            # Task model with risk/delay prediction methods
│   ├── views.py             # Views with ORM queries & pagination
│   ├── forms.py             # TaskForm with server-side validation
│   ├── auth_views.py        # Registration, login, logout (POST-only)
│   ├── auth_forms.py        # User registration & login forms
│   ├── admin.py             # Admin panel configuration
│   ├── urls.py              # URL routing
│   └── tests.py             # Unit tests (model, view, form)
├── templates/tasks/         # HTML templates
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## License

This project is for educational purposes.
