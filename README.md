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
## Endpoints
 
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/token/` | Obtain JWT access and refresh tokens |
| POST | `/api/token/refresh/` | Refresh access token |
| GET | `/api/branches/` | List all branches |
| GET | `/api/branches/{id}/stock-summary/` | Stock summary for a branch |
| GET | `/api/transfers/` | List all transfers (with filters) |
| POST | `/api/transfers/` | Create a stock transfer |
| POST | `/api/transfers/{id}/approve/` | Approve or reject a transfer |
 
### Transfer list filters
 
```
/api/transfers/?transfer_status=PENDING
/api/transfers/?from_branch__code=BR123ABC
/api/transfers/?to_branch__code=BR456DEF
/api/transfers/?product__sku=SKUXXXXXXX
```
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
>>>>>>> 01f1dc4 (docs: postman collection)
