# SmartFix Complaint Management System

A Django-based complaint management system for tracking, managing, and resolving complaints efficiently.


git clone <repository-url>

cd SmartFix_Complaint_Management_System

python -m venv env

env\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver

If all commands execute successfully, the application will be available at:

http://127.0.0.1:8000/

Admin Panel:

http://127.0.0.1:8000/admin/

## Features

* User Registration and Authentication
* Complaint Creation and Tracking
* Complaint Status Management
* Admin Dashboard with Analytics
* User Profile Management
* Notifications System
* Reports and CSV Export
* Image Upload Support
* Responsive User Interface

---

## Admin Access

Create an admin user:

```bash
python manage.py createsuperuser
```

Access the admin panel:

```text
http://127.0.0.1:8000/admin/
```

---

## Project Structure

```text
SmartFix_Complaint_Management_System/
│
├── complaints/          # Main Django application
├── config/              # Django project configuration
├── templates/           # HTML templates
├── static/              # CSS, JavaScript, Images
├── media/               # User uploaded files
├── manage.py            # Django management script
├── requirements.txt     # Project dependencies
├── README.md            # Project documentation
└── db.sqlite3           # SQLite database (generated automatically)
```

---

## Common Commands

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Migrations

```bash
python manage.py migrate
```

### Check Project for Errors

```bash
python manage.py check
```

### Open Django Shell

```bash
python manage.py shell
```

### Create Superuser

```bash
python manage.py createsuperuser
```

### Collect Static Files (Production)

```bash
python manage.py collectstatic
```

---

## Requirements

* Python 3.10+
* Django 5.2+
* Dependencies listed in `requirements.txt`

---

## Notes

The following files and folders should **not** be uploaded to GitHub:

```text
env/
__pycache__/
*.pyc
db.sqlite3
.vscode/
```
These files are automatically recreated when the setup steps above are followed.


