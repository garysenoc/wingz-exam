# Wingz Ride Management API

A RESTful API built with Django REST Framework for managing ride information. This project implements a ride-sharing backend with optimized queries, role-based access control, and a clean DDD-lite architecture.

## Quick Start

### Prerequisites

- Python 3.13+
- pip
- git

### 1. Clone and enter the project

```bash
git clone https://github.com/your-username/django-wingz.git
cd django-wingz
```

### 2. Create a virtual environment

```bash
python3 -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the database

```bash
python manage.py migrate
```

### 5. Create an admin account and sample data

```bash
python manage.py seed_data
```

You'll see output like this — save the token:

```
Seeding database...
  Admin created. Token: abc123your-token-here
Seeding complete!
```

This creates:
- An admin user: username `admin`, password `admin123`
- Sample riders, drivers, rides, and ride events
- An API token printed in the terminal

> If you prefer to create your own superuser instead, see [Manual Setup](#manual-setup) below.

### 6. Start the server

```bash
python manage.py runserver
```

### 7. You're ready!

Open one of these in your browser:

| URL | What you get |
|-----|-------------|
| http://127.0.0.1:8000/api/docs/ | Swagger UI — try out all endpoints interactively |
| http://127.0.0.1:8000/api/redoc/ | ReDoc — clean, readable API docs |
| http://127.0.0.1:8000/admin/ | Django admin panel (login: `admin` / `admin123`) |

### Managing Users via Django Admin

1. Go to http://127.0.0.1:8000/admin/ and log in (`admin` / `admin123`)
2. Click **Users** under the RIDES section
3. Click **Add User** in the top right
4. Fill in:
   - **Username** and **Password** (required)
   - Click **Save and continue editing**
5. On the next screen, fill in:
   - **First name**, **Last name**, **Email**
   - **Role** — pick `admin`, `rider`, or `driver`
   - **Phone number** (optional)
6. Click **Save**

To give a user API access, you also need to create a token:
1. Go back to the admin home
2. Click **Tokens** under the AUTH TOKEN section
3. Click **Add Token**, select the user, and click **Save**
4. The token key is now shown — use it for API requests

## Using the API

### Option 1: Swagger UI (recommended for exploring)

1. Go to http://127.0.0.1:8000/api/docs/
2. Click the **Authorize** button (lock icon at the top)
3. In the value field, type exactly:
   ```
   Token abc123your-token-here
   ```
   (Replace with your actual token. The word `Token` + a space + your key is required.)
4. Click **Authorize**, then **Close**
5. Now you can expand any endpoint and click **Try it out** then **Execute**

### Option 2: curl

```bash
# List all rides
curl http://127.0.0.1:8000/api/rides/ \
  -H "Authorization: Token abc123your-token-here"

# Filter by status
curl "http://127.0.0.1:8000/api/rides/?status=pickup" \
  -H "Authorization: Token abc123your-token-here"

# Get a token from username/password
curl -X POST http://127.0.0.1:8000/api-token-auth/ \
  -d "username=admin&password=admin123"
```

### Option 3: Browsable API

1. Go to http://127.0.0.1:8000/api-auth/login/
2. Log in with `admin` / `admin123`
3. Visit http://127.0.0.1:8000/api/rides/ in your browser

## API Reference

### Rides

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/rides/` | List all rides |
| POST | `/api/rides/` | Create a ride |
| GET | `/api/rides/{id}/` | Retrieve a ride |
| PUT | `/api/rides/{id}/` | Update a ride |
| PATCH | `/api/rides/{id}/` | Partially update a ride |
| DELETE | `/api/rides/{id}/` | Delete a ride |

### Users

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/users/` | List all users |
| POST | `/api/users/` | Create a user |
| GET | `/api/users/{id}/` | Retrieve a user |
| PUT | `/api/users/{id}/` | Update a user |
| DELETE | `/api/users/{id}/` | Delete a user |

### Authentication

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api-token-auth/` | Get a token (send `username` and `password`) |

### Filtering

```
GET /api/rides/?status=pickup
GET /api/rides/?rider_email=alice@example.com
GET /api/rides/?status=pickup&rider_email=alice@example.com
```

### Sorting

Sort by pickup time:

```
GET /api/rides/?sort_by=pickup_time&order=asc
GET /api/rides/?sort_by=pickup_time&order=desc
```

Sort by distance from a GPS position (closest first):

```
GET /api/rides/?sort_by=distance&latitude=34.0522&longitude=-118.2437
```

The distance calculation happens entirely in the database using the Spherical Law of Cosines, so it works with pagination and scales to large datasets.

### Pagination

Default page size is 10. Customizable up to 100.

```
GET /api/rides/?page=2&page_size=20
```

Response includes `count`, `next`, and `previous` links.

## Project Structure

The project follows a DDD-lite (pragmatic Domain-Driven Design) architecture:

```
rides/
├── models.py           # Domain entities — data definitions
├── selectors.py        # Read operations — how to query data
├── services.py         # Write operations — business logic
├── serializers.py      # Presentation — JSON shape for API responses
├── views.py            # Thin controllers — parse request, delegate, respond
├── permissions.py      # Access control — admin-only enforcement
├── urls.py             # Routing
├── admin.py            # Django admin panel config
├── tests/
│   ├── conftest.py     # Shared fixtures (admin user, API client, etc.)
│   ├── factories.py    # Test data factories using factory-boy
│   ├── test_models.py
│   ├── test_selectors.py
│   ├── test_services.py
│   ├── test_permissions.py
│   ├── test_serializers.py
│   └── test_views.py
└── management/
    └── commands/
        └── seed_data.py
```

Why this over a standard Django layout:

- **selectors.py** — all query optimization in one place. Need a new filter? Add it here.
- **services.py** — all write logic in one place. Creating a ride auto-logs a RideEvent here.
- **views.py** — stays thin. Parses params, calls a selector or service, returns the response.

## Design Decisions

### Performance: 2 queries for the Ride List

The ride list endpoint uses exactly 2 queries (3 including the pagination count):

1. **Query 1**: Rides + rider + driver in one query via `select_related` (SQL JOIN).
2. **Query 2**: Today's ride events via `Prefetch` with a filtered queryset — only loads events from the last 24 hours, never the full table.

### Distance sorting in the database

The Spherical Law of Cosines formula is expressed using Django ORM expressions (`ACos`, `Cos`, `Sin`, `Radians`). The database does the math and sorts, so pagination works correctly even on very large tables.

### Composite indexes

- `ride_event(id_ride, -created_at)` — covers the Prefetch query's filter + sort in a single index scan.
- `ride(status, -pickup_time)` — covers status filtering + time sorting together.

### Why DDD-lite

Django is opinionated. Wrapping the ORM in repository abstractions adds complexity without real benefit at this scale. DDD-lite borrows the useful parts — separating reads (selectors) from writes (services) — while staying idiomatic to Django.

## Running Tests

```bash
# Run all 91 tests
python -m pytest -v

# Run with coverage
coverage run -m pytest -v
coverage report -m --include="rides/*.py" --omit="rides/tests/*,rides/migrations/*"

# HTML coverage report
coverage html --include="rides/*.py" --omit="rides/tests/*,rides/migrations/*"
open htmlcov/index.html
```

Current status: **91 tests, 98% coverage**.

## Linting and Code Quality

```bash
# Setup (one-time, after git init)
pre-commit install
pre-commit install --hook-type commit-msg

# Run manually
ruff check rides/ --fix     # lint
ruff format rides/           # format
mypy rides/                  # type check
```

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/), enforced by commitizen:

```
feat: add ride filtering by status
fix: correct distance calculation edge case
test: add coverage for ride event prefetch
```

## Bonus: SQL Query

Count of trips that took more than 1 hour from pickup to dropoff, by month and driver:

```sql
SELECT
    strftime('%Y-%m', pickup_event.created_at) AS month,
    u.first_name || ' ' || substr(u.last_name, 1, 1) AS driver,
    COUNT(*) AS "count_of_trips_gt_1hr"
FROM ride r
JOIN "user" u ON u.id_user = r.id_driver
JOIN ride_event pickup_event
    ON pickup_event.id_ride = r.id_ride
    AND pickup_event.description = 'Status changed to pickup'
JOIN ride_event dropoff_event
    ON dropoff_event.id_ride = r.id_ride
    AND dropoff_event.description = 'Status changed to dropoff'
WHERE (julianday(dropoff_event.created_at) - julianday(pickup_event.created_at)) * 24 > 1
GROUP BY month, driver
ORDER BY month, driver;
```

### How to run this query

Open the database shell:

```bash
python manage.py dbshell
```

Then paste the SQL query above and press Enter. Expected output:

```
Month        Driver               Count of Trips > 1hr
----------------------------------------------------
2026-01      Chris H              2
2026-01      Howard Y             1
2026-02      Chris H              1
2026-02      Howard Y             1
```

> Note: You need to run `python manage.py seed_data` first to populate the database with sample data that includes rides with pickup and dropoff events spanning over 1 hour.

### PostgreSQL version

```sql
SELECT
    to_char(pickup_event.created_at, 'YYYY-MM') AS month,
    u.first_name || ' ' || left(u.last_name, 1) AS driver,
    COUNT(*) AS "count_of_trips_gt_1hr"
FROM ride r
JOIN "user" u ON u.id_user = r.id_driver
JOIN ride_event pickup_event
    ON pickup_event.id_ride = r.id_ride
    AND pickup_event.description = 'Status changed to pickup'
JOIN ride_event dropoff_event
    ON dropoff_event.id_ride = r.id_ride
    AND dropoff_event.description = 'Status changed to dropoff'
WHERE dropoff_event.created_at - pickup_event.created_at > INTERVAL '1 hour'
GROUP BY month, driver
ORDER BY month, driver;
```

## Manual Setup

If you prefer to create your own superuser instead of using `seed_data`:

```bash
# 1. Create superuser (will prompt for username, email, password)
python manage.py createsuperuser

# 2. Set the admin role and get your token
python manage.py shell
```

Then in the shell:

```python
from rides.models import User
from rest_framework.authtoken.models import Token

user = User.objects.get(username="your_username_here")  # replace with your username
user.role = "admin"
user.save()

token, _ = Token.objects.get_or_create(user=user)
print(f"Your token: {token.key}")
# exit() to leave the shell
```

> Important: The API requires `role='admin'`. The `createsuperuser` command does not set this automatically — you must run the shell commands above.

## Troubleshooting

**"Only users with the admin role can access this API."**
- Your user exists but their `role` is not `admin`. Run:
  ```bash
  python manage.py shell -c "
  from rides.models import User
  u = User.objects.get(username='admin')
  print(f'Role: {u.role}')
  "
  ```
- If the role is not `admin`, set it: `u.role = 'admin'; u.save()`

**"Authentication credentials were not provided."**
- You didn't include a token. Make sure your header is:
  ```
  Authorization: Token abc123your-token-here
  ```
- In Swagger: click **Authorize** and enter `Token <your-key>` (the word Token + space + key).

**"Invalid token."**
- The token doesn't exist in the database. Generate a new one:
  ```bash
  python manage.py shell -c "
  from rest_framework.authtoken.models import Token
  from rides.models import User
  token, _ = Token.objects.get_or_create(user=User.objects.get(username='admin'))
  print(token.key)
  "
  ```

**Swagger "Execute" button is greyed out**
- You need to click **Try it out** first, then **Execute** becomes active.

**Port already in use**
- Kill the existing process: `lsof -ti:8000 | xargs kill`
- Or use a different port: `python manage.py runserver 8080`

## Tech Stack

- Python 3.13
- Django 6.0
- Django REST Framework 3.17
- drf-spectacular (Swagger/OpenAPI)
- SQLite (dev) — swap to PostgreSQL for production
- pytest + factory-boy for testing
- coverage for test coverage
- ruff for linting/formatting
- mypy for type checking
- pre-commit + commitizen for git hooks
# wingz-exam
