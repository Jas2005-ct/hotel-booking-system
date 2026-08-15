# Hotel Booking & Management System

A full-featured hotel management platform built with **Django 5**, covering user registration/login, menu management, table reservation, order processing (guest → kitchen → waiter), and an admin dashboard with live analytics.

## Features

- **Role-based access** — four built-in roles with scoped permissions (admin, guest, kitchen staff, waiter)
  - `admin` — full access: menu CRUD, table management, reports, user management
  - `guest` — view menu, manage cart, place orders, reserve tables
  - `kitchen` — view incoming orders, prepare & mark orders ready
  - `waiter` — assign tables, deliver orders, mark orders completed
- **Menu management** — add/update/delete dishes with images, price, veg/non-veg, and food category
- **Table reservation** — book tables with automatic conflict detection, seat capacity matching, and table availability tracking
- **Order workflow** — cart → checkout → kitchen queue → ready → completed, with order history per user
- **Cloudflare R2 media storage** — menu images served from a Cloudflare R2 bucket (S3-compatible) with lazy loading
- **Async email notifications** — welcome email, order confirmation, reservation confirmation, and 1-hour reminders (via Celery)
- **Admin dashboard** — revenue, order counts by status, top-selling items, category sales, live orders, and AJAX-powered data tables

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5, Python 3.11–3.12 |
| Database | PostgreSQL (Supabase), falls back to SQLite locally |
| Media storage | Cloudflare R2 via `django-storages` + `boto3` |
| Async tasks | Celery + Redis (results & beat) |
| Cache | Redis (`django-redis`) |
| Frontend | Django templates, Bootstrap 5, Crispy Forms, AJAX |
| Data tables | `django-ajax-datatable` |
| Dependency mgmt | Poetry |

## Project Structure

```
hotel-booking-system/
├── accounts/              # CustomUser, Menu, TableLayout models; auth & menu/table views
├── table_reservation/     # TableReservation, TableAssign; booking, assignment views & tasks
├── orders/                # Cart_User, Cart_Items, Order, OrderItem, OrderKitchenStaff; order workflow
├── admin_report/          # Admin dashboard, order/table listing, live orders
├── common/                # Shared mixins & decorators (role checks)
├── project_files/         # Django project (settings, urls, celery, storages)
├── templates/             # Shared/base templates
├── static/                # Static assets
└── media/                 # Local media fallback (used when R2 is disabled)
```

## Getting Started

### Prerequisites

- Python 3.11 or 3.12
- [Poetry](https://python-poetry.org/docs/#installation)
- Redis (for Celery) — optional if you run without async tasks
- A Supabase PostgreSQL project (optional — SQLite is the fallback)
- A Cloudflare R2 bucket (optional — local filesystem is the fallback)

### Installation

```bash
# 1. Clone and enter the repo
git clone https://github.com/Jas2005-ct/hotel-booking-system.git
cd hotel-booking-system

# 2. Install dependencies
poetry install

# 3. Configure environment
cp .env.example .env
#  edit .env with your SECRET_KEY, DATABASE_URL, R2_*, and email settings

# 4. Apply migrations
poetry run python manage.py migrate

# 5. (Optional) seed default groups & permissions
poetry run python manage.py migrate accounts  # already applied by step 4

# 6. Run the dev server
poetry run python manage.py runserver
```

Open http://127.0.0.1:8000/

### Creating users

Register through the public pages, or create users from the shell:

```bash
poetry run python manage.py shell -c "from accounts.models import CustomUser, RoleChoices; CustomUser.objects.create_user('admin@example.com', 'password123', name='Admin', phone_no='+919876543210', role=RoleChoices.ADMIN)"
```

> **Note:** `guest` / `waiter` / `admin` users are added to their matching auth groups automatically on registration so they inherit the correct permissions.

## Configuration (.env)

| Variable | Purpose | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (`True`/`False`) | Yes |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | Yes |
| `DATABASE_URL` | PostgreSQL URL, e.g. `postgresql://user:pass@host:5432/dbname`. Leave empty for SQLite | No |
| `REDIS_URL` | Redis URL used by Celery results/cache | For async |
| `CELERY_RESULT_BACKEND` | Redis DB for Celery results | For async |
| `EMAIL_HOST` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_PORT` | SMTP settings (e.g. Mailtrap) | For emails |
| `R2_ACCOUNT_ID` | Cloudflare account ID | For R2 |
| `R2_BUCKET_NAME` | R2 bucket name. Leave empty to use local filesystem | No |
| `R2_ACCESS_KEY_ID` | R2 access key ID | For R2 |
| `R2_SECRET_ACCESS_KEY` | R2 secret access key | For R2 |
| `R2_PUBLIC_URL` | R2 public hostname (e.g. `pub-xxxx.r2.dev` — **hostname only**, no `https://` or path) | For R2 |

## Running Celery (async tasks)

Start two processes alongside the web server:

```bash
poetry run celery -A project_files worker --loglevel=info
poetry run celery -A project_files beat --loglevel=info
```

Celery beat runs two scheduled jobs every minute:

- `reminder_before_one_hour` — sends guests a reminder 1 hour before their reservation
- `change_table_status` — auto-marks tables unavailable when a reservation starts

## Database

- Defaults to SQLite (`db.sqlite3`) when `DATABASE_URL` is unset.
- When `DATABASE_URL` is set, the app connects to PostgreSQL with `sslmode=require` and a 20s connect timeout.
- Run `poetry run python manage.py migrate` after pulling new migrations.

## Media Storage (Cloudflare R2)

Menu images upload to a Cloudflare R2 bucket when `R2_BUCKET_NAME` is configured:

- The database stores only the relative path (e.g. `menu_images/Biriyani.jpg`).
- Templates render `{{ menu.images.url }}`, which resolves to the R2 public URL at render time.
- Images are downscaled to ~800px wide before upload to keep pages fast, and load lazily in the browser.
- Leave `R2_BUCKET_NAME` empty to store files locally under `media/`.

## Contributing

1. Branch off `development`: `git checkout -b feature/your-feature development`
2. Make changes and commit with a descriptive message
3. Push and open a pull request against `development`

## License

MIT
