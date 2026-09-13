# Airport API Service

Django + Django REST Framework API для авіакомпанії: країни, міста, аеропорти,
типи літаків, літаки, екіпаж, маршрути, рейси та замовлення з квитками.
Автентифікація — JWT (кастомна модель користувача з логіном по email).

## Стек

- Python 3.13, Django 6.1.1, Django REST Framework 3.18.1
- `djangorestframework-simplejwt` — JWT-автентифікація
- `drf-spectacular` — автогенерація OpenAPI-схеми та Swagger/Redoc UI
- `pillow` — обробка зображень (фото літаків)
- PostgreSQL 16 (`psycopg`), Docker + docker-compose

## Встановлення та запуск (Docker)

Проєкт запускається через Docker Compose: контейнер з Django-застосунком
(`airport`) і контейнер з PostgreSQL (`airport_app_db`).

```bash
git clone <repo-url>
cd airport_API_service

cp .env_example .env   # заповнити своїми значеннями (SECRET_KEY, POSTGRES_*)

docker compose up -d --build
```

API буде доступне на `http://127.0.0.1:8000/`.

Створити суперкористувача (опційно, для доступу в Django admin):

```bash
docker compose exec airport python manage.py createsuperuser
```

### Наповнення тестовими даними

```bash
docker compose exec airport python manage.py seed_db
```

## Документація API

- Swagger UI: `/api/doc/swagger/`
- Redoc: `/api/doc/redoc/`
- OpenAPI-схема (JSON/YAML): `/api/doc/`

## Автентифікація

Реєстрація та отримання JWT-токенів:

| Метод | Ендпоінт | Опис |
|---|---|---|
| POST | `/api/user/register/` | Реєстрація нового користувача |
| POST | `/api/user/login/` | Отримати пару access/refresh токенів |
| POST | `/api/user/refresh/` | Оновити access-токен |
| POST | `/api/user/verify/` | Перевірити валідність токена |
| GET/PUT/PATCH | `/api/user/me/` | Переглянути/оновити власний профіль |

Для запитів до захищених ендпоінтів передавайте заголовок:

```
Authorization: Bearer <access_token>
```

## Основні ендпоінти

Базовий шлях: `/api/airport/`

| Ресурс | Ендпоінт | Права |
|---|---|---|
| Країни | `countries/` | читання — будь-який автентифікований, запис — admin |
| Міста | `cities/` | те саме |
| Аеропорти | `airports/` | те саме |
| Типи літаків | `airplane-types/` | те саме |
| Літаки | `airplanes/` | те саме; `POST airplanes/{id}/upload-image/` — лише admin |
| Екіпаж | `crew/` | те саме |
| Маршрути | `routes/` | те саме |
| Рейси | `flights/` | те саме |
| Замовлення | `orders/` | лише автентифіковані, кожен бачить тільки свої замовлення |

Усі list-ендпоінти пагіновані (`PageNumberPagination`, 10 записів на сторінку) —
відповідь має вигляд `{"count", "next", "previous", "results"}`.

### Фільтри

- `GET /api/airport/routes/?city=<назва>` — маршрути за назвою міста відправлення (icontains)
- `GET /api/airport/flights/?source=<назва>&destination=<назва>&departure_date=YYYY-MM-DD`
- `GET /api/airport/airplanes/?airplane_type=<id1,id2>`

## Тести

```bash
docker compose exec airport python manage.py test airport.tests
```

## Обмеження частоти запитів (throttling)

- Анонімні користувачі: 10 запитів/день
- Автентифіковані користувачі: 100 запитів/день

## Схема БД

ER-діаграма моделей: [`models_chema/airport_models.png`](models_chema/airport_models.png).

## Форматування коду

Стиль коду підтримується `ruff` (конфіг — `ruff.toml`, `line-length = 79`).
