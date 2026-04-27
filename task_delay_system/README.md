# TaskFlow — Task Delay System

A production-grade Django task management system featuring real-time WebSocket notifications, FSM-enforced workflow, predictive risk scoring, and role-based access control.

**Live Demo:** https://task-delay-system.onrender.com

---

## Features

- **Role-Based Access Control** — Employees and Managers with separate permission gates enforced at the service layer
- **FSM Workflow** — `PENDING → IN_PROGRESS → READY_FOR_REVIEW → APPROVED / REJECTED` with strict transition enforcement
- **Real-Time Notifications** — WebSocket notifications via Django Channels/Daphne (employee submits → manager notified; manager approves/rejects → employee notified)
- **Risk Scoring** — 0–100 risk score computed via ORM annotations based on deadline proximity and priority
- **REST API** — Full DRF API with JWT authentication, Swagger UI at `/api/docs/`, idempotency key support
- **Celery Background Tasks** — Daily manager digest email and hourly employee reminders (design; requires Redis broker)
- **Audit Logging** — Every task mutation is logged to `AuditLog` via Django signals
- **Dashboard Analytics** — KPI cards, team workload breakdown, status distribution, risk breakdown
- **Department Management** — Superuser-managed departments with employee assignments

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 |
| ASGI Server | Daphne 4.0 |
| Database | PostgreSQL (via psycopg2) |
| Real-Time | Django Channels 4 + InMemoryChannelLayer |
| REST API | Django REST Framework 3.14 + SimpleJWT |
| Background Tasks | Celery 5.3 + Redis (broker) |
| Task Scheduling | Celery Beat + django-celery-beat |
| Static Files | WhiteNoise |
| Deployment | Render |

---

## Quick Start (Local)

### 1. Clone & Create Virtual Environment

```bash
git clone https://github.com/OPap-12/Task-Delay-system.git
cd Task-Delay-system/task_delay_system
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the template and fill in your values:

```bash
cp .env.example .env
```

Key variables in `.env`:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (required) |
| `DEBUG` | `True` for local, `False` for production |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis URL for Celery (optional locally) |

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Start Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — log in or register to start.

> **Note:** For WebSocket support locally, use `daphne task_delay_system.asgi:application` instead of `runserver`.

---

## Running Tests

```bash
python manage.py test tasks -v2
```

All 32 tests should pass covering: model FSM logic, risk scoring, form validation, view authentication, and workflow transitions.

---

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/tasks/` | List tasks (filtered by role) |
| `POST /api/v1/tasks/` | Create task (manager only) |
| `PATCH /api/v1/tasks/{id}/status/` | FSM state transition |
| `GET /api/v1/dashboard/metrics/` | Dashboard KPIs |
| `GET /api/v1/profile/` | Current user profile |
| `POST /api/token/` | Obtain JWT token |
| `POST /api/token/refresh/` | Refresh JWT token |
| `GET /api/docs/` | Swagger UI |

---

## Project Structure

```
task_delay_system/
├── task_delay_system/       # Project config
│   ├── settings.py          # Env-based config (python-decouple)
│   ├── urls.py              # Root URL routing
│   ├── asgi.py              # ASGI + WebSocket routing
│   └── celery.py            # Celery app + beat schedule
├── tasks/                   # Main application
│   ├── models.py            # Task FSM, risk scoring, AuditLog
│   ├── views.py             # Django views with RBAC
│   ├── api_views.py         # DRF ViewSets
│   ├── services/
│   │   └── task_service.py  # Centralized business logic + RBAC
│   ├── consumers.py         # WebSocket consumer (Channels)
│   ├── forms.py             # TaskForm, DepartmentForm
│   ├── auth_views.py        # Login, register, logout
│   ├── serializers.py       # DRF serializers
│   ├── signals.py           # Audit log signals
│   ├── tasks.py             # Celery async tasks
│   ├── admin.py             # Django admin config
│   ├── urls.py              # App URL routing
│   └── tests.py             # 32 unit tests
├── templates/               # Django HTML templates
├── static/                  # CSS, JS (ES6 modules)
│   └── tasks/
│       ├── css/modern_style.css
│       └── js/
│           ├── main.js      # Entry point, WebSocket init
│           ├── ws.js        # WebSocket client + reconnect
│           ├── api.js       # Fetch wrapper + event bus
│           ├── actions.js   # FSM action dispatcher
│           └── state.js     # In-memory task state cache
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Demo Credentials

See `user_credentials.md` for a full list of test accounts.

| Username | Role | Password |
|----------|------|----------|
| `admin_main` | Superuser | `Admin@1234` |
| `user1_matthew` | Manager | `Pass@1001` |
| `user4_barbara` | Employee | `Pass@1004` |

---

## License

This project is for educational/portfolio purposes.
