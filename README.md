# TaskManager — Multi-Tenant Task Lifecycle & Workflow Management Engine

[![Django](https://img.shields.io/badge/Django-5.2+-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![WhiteNoise](https://img.shields.io/badge/Static-WhiteNoise-informational?style=for-the-badge)](http://whitenoise.evans.io/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 1. Project Overview

**TaskManager** is a clean, production-oriented task lifecycle management web application built on Django 5.2. Engineered with strict row-level isolation and defense-in-depth authorization patterns, TaskManager delivers responsive task triage, multi-dimensional query filtering, full-text search, live status tracking, and single-query telemetry aggregation. 

The architecture guarantees tenant data isolation where users cannot view, edit, toggle, or delete tasks belonging to other accounts, paired with zero-downtime database deployment capability across SQLite (local development) and PostgreSQL (production).

---

## 2. Tech Stack & Dependencies

| Layer | Technology | Details |
|---|---|---|
| **Web Framework** | Django 5.2.4 | MVT architecture, Class-Based Views (CBVs), ORM |
| **Runtime** | Python 3.11 / 3.12 / 3.13 | Strict typing and modern standard library features |
| **Database** | SQLite (Local) / PostgreSQL (Prod) | Configured via `dj-database-url` with connection pooling |
| **Static Assets** | WhiteNoise 6.9.0 | `CompressedManifestStaticFilesStorage` for cache-busted delivery |
| **Forms & Styling** | Django Crispy Forms & Crispy Bootstrap 5 | Semantic form layouts with custom UI widgets and badges |
| **WSGI Server** | Gunicorn 23.0.0 | Production-grade multi-worker application server |
| **Environment Config** | Python-Dotenv 1.1.1 & Decouple | 12-factor configuration via `.env` |

---

## 3. Architecture & Directory Layout

```
taskmanager/
├── manage.py                   # Django management CLI utility
├── Procfile                    # Deployment process definition (web: gunicorn)
├── requirements.txt            # Locked project dependencies
├── .env                        # Local environment variables (git-ignored)
├── db.sqlite3                  # Development SQLite database
├── taskmanager/                # Core project orchestration root
│   ├── __init__.py
│   ├── settings.py             # Security settings, WhiteNoise, DB router
│   ├── urls.py                 # Root URL configuration delegating to tasks
│   ├── wsgi.py                 # WSGI production server entry point
│   └── asgi.py                 # ASGI asynchronous entry point
├── tasks/                      # Core task management domain application
│   ├── models.py               # Task model with db indexes and choices
│   ├── views.py                # CBVs (List, Detail, Create, Update, Delete) & status toggle
│   ├── forms.py                # TaskForm with custom bootstrap widgets and emoji badges
│   ├── urls.py                 # Route mappings for CRUD & authentication
│   ├── admin.py                # Django administrative registrations
│   ├── apps.py                 # Tasks app configuration
│   └── templates/              # Semantic HTML5 views (home, task_list, form, auth)
└── static/                     # CSS stylesheets, JavaScript helpers, and branding
```

---

## 4. Key Engineering Highlights & Security Decisions

### 🛡️ Row-Level Authorization & Query Isolation
- **Problem**: In multi-user web systems, improper object querying frequently results in Insecure Direct Object References (IDOR), allowing malicious users to view or manipulate other users' data by enumerating integer primary keys.
- **Solution**: 
  - `TaskListView.get_queryset()` strictly scopes all database reads to `Task.objects.filter(user=self.request.user)`.
  - In `TaskDetailView`, `TaskUpdateView`, and `TaskDeleteView`, `get_object()` overrides verify ownership against `self.request.user` and explicitly raise `PermissionDenied` (HTTP 403) on unauthorized access attempts.
  - State mutation via `toggle_complete` utilizes `get_object_or_404(Task, pk=pk, user=request.user)`.

### ⚡ Aggregated Sidebar Telemetry in a Single Query
- **Problem**: Generating sidebar counts for `todo`, `in_progress`, and `done` categories via separate `.filter().count()` calls issues multiple sequential database queries (`3x SQL roundtrips`) on every page load.
- **Solution**:
  - Implemented aggregation using Django ORM `.values('status').annotate(total=Count('id'))`.
  - Consolidates all metrics into **one single SQL query**, mapping results in memory via a status hash map.

### 🔍 Optimized Query Filtering & Database Indexes
- High-frequency query columns (`priority`, `status`) feature explicit database indexes (`db_index=True`) on the `Task` model to ensure sub-millisecond retrieval on large datasets.
- Multi-field search executes case-insensitive filtering across title and description using `Q(title__icontains=search) | Q(description__icontains=search)`.

### 🚀 Production Deployment Readiness
- Pre-configured `Procfile` for immediate deployment on platforms like Render or Railway.
- Database auto-swapping: seamlessly reads `DATABASE_URL` in production (e.g., Supabase, Neon, AWS RDS PostgreSQL) with persistent connection reuse (`conn_max_age=600`), falling back to local SQLite when unset.
- Static file compression and fingerprint hashing handled seamlessly by WhiteNoise.

---

## 5. Data Model Specification

### **Task** (`tasks.models.Task`)

| Field | Type | Attributes / Constraints | Description |
|---|---|---|---|
| `id` | `BigAutoField` | `primary_key=True` | Unique auto-incrementing task identifier |
| `user` | `ForeignKey` | `to=AUTH_USER_MODEL`, `on_delete=CASCADE`, `related_name='tasks'` | Task owner enforcing strict ownership boundary |
| `title` | `CharField` | `max_length=200` | Human-readable title of the task |
| `description` | `TextField` | `blank=True` | Detailed task instructions or notes |
| `priority` | `CharField` | `max_length=10`, `choices=['low', 'medium', 'high']`, `default='medium'`, `db_index=True` | Priority classification with database index |
| `status` | `CharField` | `max_length=20`, `choices=['todo', 'in_progress', 'done']`, `default='todo'`, `db_index=True` | Workflow status lifecycle state |
| `completed` | `BooleanField` | `default=False` | Fast boolean indicator synchronized with status |
| `due_date` | `DateTimeField` | `null=True`, `blank=True` | Deadline timestamp for task execution |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Creation audit timestamp (default sort `-created_at`) |
| `updated_at` | `DateTimeField` | `auto_now=True` | Last modification audit timestamp |

---

## 6. Application Routes & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | Task dashboard and paginated task management table | Yes (Redirects to `/login/`) |
| `GET`, `POST` | `/task/new/` | Task creation modal and submission form | Yes |
| `GET` | `/task/<id>/` | Detailed task view with metadata | Yes (Owner only) |
| `GET`, `POST` | `/task/<id>/edit/` | Task editing and status modification form | Yes (Owner only) |
| `GET`, `POST` | `/task/<id>/delete/` | Task deletion confirmation and execution | Yes (Owner only) |
| `GET`, `POST` | `/task/<id>/toggle/` | Quick toggle between completed and incomplete | Yes (Owner only) |
| `GET`, `POST` | `/signup/` | New user account registration | No |
| `GET`, `POST` | `/login/` | User session authentication | No |
| `GET`, `POST` | `/logout/` | Terminate session and redirect | Yes |
| `GET`, `POST` | `/admin/` | Django administrative interface | Staff / Superuser |

---

## 7. Environment Variables Configuration

Create a `.env` file in the project root:

```env
# Django Security
SECRET_KEY=your-secure-random-secret-key-here
DEBUG=True

# Hostnames (comma-separated)
ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com

# Production Database (Optional: falls back to SQLite if omitted)
# DATABASE_URL=postgres://user:password@hostname:5432/dbname
```

---

## 8. Local Installation & Setup

### Prerequisites
- Python 3.11+
- Git

### Step-by-Step Instructions

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd taskmanager
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize environment configuration**:
   ```bash
   # Create your local .env file
   cp .env.example .env   # Or create .env with the settings above
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create an administrator superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**:
   ```bash
   python manage.py runserver
   ```
   Open your browser and navigate to `http://127.0.0.1:8000/`.

---

## 9. Production Deployment Guidelines

1. **Static Files**:
   ```bash
   python manage.py collectstatic --no-input
   ```
2. **Launch WSGI Server**:
   ```bash
   gunicorn taskmanager.wsgi:application --bind 0.0.0.0:$PORT
   ```
3. Set `DEBUG=False` and supply a strong, randomly-generated `SECRET_KEY` in your production environment settings.
