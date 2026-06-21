# SmartFix Complaint Management System

A Django-based complaint management system for tracking, managing, and resolving complaints efficiently.

#Quick Start

1. Clone Repository
git clone <repository-url>
cd SmartFix_Complaint_Management_System
2. Create Virtual Environment
python -m venv env
3. Activate Virtual Environment

Windows:

env\Scripts\activate

Linux/macOS:

source env/bin/activate
4. Install Dependencies
pip install -r requirements.txt
5. Run Migrations
python manage.py migrate
6. Create Admin User
python manage.py createsuperuser
7. Run Server
python manage.py runserver
8. Open Application
http://127.0.0.1:8000/

Admin Panel:

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
