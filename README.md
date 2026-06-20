# SmartFix Complaint Management System

A Django-based complaint management system for tracking, managing, and resolving complaints efficiently.

## Quick Start
## Quick Start

### 1. Create Virtual Environment

```bash
python -m venv env
```

### 2. Activate Virtual Environment

Windows:

```bash
env\Scripts\activate
```

Linux / macOS:

```bash
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
python manage.py migrate
```

### 5. Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

### 6. Start the Server

```bash
python manage.py runserver
```

### 7. Access the Application

Open your browser and go to:

```text
http://127.0.0.1:8000/
```

Admin Panel:

```text
http://127.0.0.1:8000/admin/
```


## Features

- User registration and authentication
- Complaint creation and tracking
- Admin dashboard with analytics
- User profile management
- Notifications system
- Reports and CSV export

## Admin Access

Create admin user:
```bash
python manage.py createsuperuser
```

Access admin panel: **http://127.0.0.1:8000/admin/**

## Project Structure

```
complaint_project/
├── complaints/          # Main Django app
├── config/              # Django settings
├── templates/           # HTML templates
├── media/               # User uploads
├── env/                 # Virtual environment
├── manage.py            # Django management
├── requirements.txt     # Dependencies
└── db.sqlite3          # Database
```

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Check for errors
python manage.py check

# Django shell
python manage.py shell

# Create superuser
python manage.py createsuperuser

# Collect static files (production)
python manage.py collectstatic
```

## Status

✅ Zero errors - Fully functional and ready to run on any system
