# HawkN Assessment API

## Tech Stack

- Python 3.13
- Django 6.0
- Django REST Framework
- SimpleJWT — authentication
- drf-spectacular — Swagger/OpenAPI docs
- django-filter — query filtering
- uv — dependency management

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/adith-p/HawknTech-test/
cd HawknTech-test
```

### 2. Install dependencies

**Using uv (recommended)**

If you don't have uv:

```bash
pip install uv
```

Then install:

```bash
uv sync
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

---

**Using pip**

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

Install dependencies:

```bash
pip install django djangorestframework djangorestframework-simplejwt django-filter drf-spectacular
```

---

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Seed the database

```bash
python manage.py seed
```

## Running Tests

```bash
python manage.py test core
```
