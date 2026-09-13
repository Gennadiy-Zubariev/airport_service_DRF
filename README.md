# Airport API Service

API service for airport management written on DRF.

## Features

- JWT authenticated
- Admin panel /admin/
- Documentation is located at /api/doc/swagger/
- Managing orders and tickets
- Creating airports with countries and cities
- Creating airplanes with types
- Adding flights with crew, routes
- Filtering flights, routes and airplanes
- Pagination for all list endpoints

## Installing using GitHub

Install PostgreSQL and create db

```bash
git clone https://github.com/<your-username>/airport_API_service.git
cd airport_API_service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Set environment variables:

```bash
set DB_HOST=<your db hostname>
set DB_NAME=<your db name>
set DB_USER=<your db username>
set DB_PASSWORD=<your db user password>
set SECRET_KEY=<your secret key>
```

Apply migrations and run server:

```bash
python manage.py migrate
python manage.py runserver
```

## Run with Docker

Docker should be installed

```bash
cp .env_example .env  # fill with your values
docker-compose build
docker-compose up
```

Create superuser (optional):

```bash
docker-compose exec airport python manage.py createsuperuser
```

Load test data (optional):

```bash
docker-compose exec airport python manage.py seed_db
```

## Getting access

- Create user via /api/user/register/
- Get access token via /api/user/login/
- Refresh token via /api/user/token/refresh/
- Verify token via /api/user/token/verify/
- Manage profile via /api/user/me/

Use the token in Authorization header:

```
Authorization: Bearer <access_token>
```

## API Endpoints

Base path: `/api/airport/`

| Resource | Endpoint | Allowed methods |
|---|---|---|
| Countries | `countries/` | GET, POST (admin) |
| Cities | `cities/` | GET, POST (admin) |
| Airports | `airports/` | full CRUD (write — admin) |
| Airplane Types | `airplane-types/` | GET, POST (admin) |
| Airplanes | `airplanes/` | full CRUD (write — admin) |
| Crew | `crew/` | full CRUD (write — admin) |
| Routes | `routes/` | full CRUD (write — admin) |
| Flights | `flights/` | full CRUD (write — admin) |
| Orders | `orders/` | GET, POST (own orders only) |

## Filters

- `GET /api/airport/routes/?city=<name>` — routes by source city name
- `GET /api/airport/flights/?source=<name>&destination=<name>&departure_date=YYYY-MM-DD`
- `GET /api/airport/airplanes/?airplane_type=<id1,id2>`

## API Documentation

- Swagger UI: `/api/doc/swagger/`
- Redoc: `/api/doc/redoc/`
- OpenAPI schema: `/api/doc/`

## DB Structure

models_schema/airport_models.png

## Tests

```bash
docker-compose exec airport python manage.py test airport.tests
```
