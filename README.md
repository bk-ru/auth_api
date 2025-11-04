# Auth Service

FastAPI-бэкенд, реализующий систему аутентификации и авторизации. Покрывает пользовательский сценарий (регистрация → вход → изменение профиля → выход).
Часть структуры файлов взял из [github](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template/tree/master/app)

## Основные возможности
Регистрация, вход, выход, обновление профиля, мягкое удаление (смена `is_active` на `false`).
Разделение аутентификации и авторизации: JWT идентифицирует пользователя, RBAC определяет разрешения. Отсутствие токена даёт `401`, недостаток прав — `403`.
Административное API: просмотр, создание, изменение и удаление ролей, привязка наборов прав.
Демонстрационные ресурсы: условные (проекты, отчёты), иллюстрирующие работу проверок.

## Стек технологий
- FastAPI / Starlette
- SQLAlchemy
- Pydantic, pydantic-settings
- Passlib (bcrypt)
- PyJWT
- PostgreSQL или SQLite для локального запуска

## Структура проекта
```
app/
|-- main.py
|-- core/                # Конфигурация и утилиты безопасности
|-- db/                  # База данных
|-- models/              # ORM-модели пользователей, ролей, прав, токенов
|-- schemas/             # Pydantic-схемы запросов и ответов
|-- services/            # Бизнес-логика работы с сущностями
|-- routers/             # Публичные эндпоинты: auth, users, resources
|-- internal/            # Административные маршруты (управление RBAC)
.env                     # Настроеки окружения
requirements.txt
```

Инициализация выполняется командой `python -m app.db.seed`, создающей роли, разрешения и администратора.

## Настройка окружения
В `.env` и заполните значения:
```
DEBUG=true
DATABASE_URL=postgresql+psycopg://auth_user:auth_pass@localhost:5432/auth_db
ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
SEED_ADMIN_EMAIL=admin@example.com
SEED_ADMIN_PASSWORD=Admin123!
```
Для быстрого старта можно использовать SQLite: `DATABASE_URL=sqlite:///./app.db`.

Клонирование проекта
```bash
git clone https://github.com/bk-ru/auth_api.git
cd auth_api
```

## Локальный запуск
```bash
pip install -r requirements.txt
python -m app.db.seed          # создание схемы и тестовых данных
uvicorn app.main:app --reload  # запуск сервера
```
Swagger UI: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

## Работа с PostgreSQL
1. Поднимите PostgreSQL.
2. Задайте строку подключения в `.env`.
3. Выполните `python -m app.db.seed` и запустите приложение.

## Пользовательские сценарии
- **Регистрация** (`POST /auth/register`) — создаёт пользователя с ролью `basic_user`, проверяет подтверждение пароля.
- **Вход** (`POST /auth/login`) — проверяет учётные данные, выпускает JWT и сохраняет токен в `access_tokens`.
- **Профиль** (`GET /users/me`) — возвращает данные текущего пользователя по валидному токену.
- **Выход** (`POST /auth/logout`) — помечает текущий токен как отозванный (`is_revoked = true`), последующие запросы с ним дают `401`.
- **Мягкое удаление** (`DELETE /users/me`) — деактивирует пользователя и отзывает все его токены.
- **Администрирование** (`/admin/*`) — управление ролями и правами, доступно только при разрешении `manage_roles`.
- **Mock-ресурсы** (`/resources/projects`, `/resources/reports`) — демонстрация проверки разрешений (`view_projects`, `edit_projects`, `view_reports`).

## Примеры запросов:
#### Регистрация (`POST /auth/register`) ![Регистрация](img/register.png)
Эндпоинт предназначен для создания нового пользователя в системе. При успешной регистрации возвращает данные созданного пользователя и его базовую роль (basic_user).

Пример запроса:
``` json
{
  "first_name": "Evgeny",
  "last_name": "Anisimov",
  "patronymic": "Alexandrovish",
  "email": "anisimov@gmail.com",
  "password": "12345678",
  "password_confirm": "12345678"
}
```

Пример ответа (201 Created):
``` json
{
  "first_name": "Evgeny",
  "last_name": "Anisimov",
  "patronymic": "Alexandrovish",
  "id": 6,
  "email": "anisimov@gmail.com",
  "is_active": true,
  "roles": ["basic_user"],
  "created_at": "2025-11-03T18:28:02.655821+03:00",
  "updated_at": "2025-11-03T18:28:02.655821+03:00"
}
```
#### Вход (`POST /auth/login`) ![Вход](img/login.png)
Эндпоинт выполняет вход пользователя в систему и возвращает JWT-токен доступа. Используется для получения авторизации перед обращением к защищённым эндпоинтам.

Пример запроса:
``` json
{
  "email": "anisimov@gmail.com",
  "password": "12345678"
}
```

Пример ответа (200 OK):
``` json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwiZXhwIjoxNzY3MTg3MzIwLCJpYXQiOjE3NjgzMjMyMjAsInJvbGUiOiJiYXNpY191c2VyIn0.rjJfky2G85biFULxjJEAh5EPwW8LbAR1vJDTxysCPU",
  "token_type": "bearer",
  "expires_in": 3599
}
```

#### Выход (`POST /auth/logout`) ![Выход](img/logout.png)

Пример запроса:
```
curl -X 'POST' \
  'http://localhost:8000/auth/logout' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwiZXhwIjoxNzY3MTgzNDQzLCJpYXQiOjE3NjgzMjMxNDMsInJvbGUiOiJiYXNpY191c2VyIn0.cxatapw7WRiNFZ8xN5XdV0iyHQc9u4D2110v_FUjJE' \
  -d ''
```
Пример ответа (204 No Content):
``` json
{}
```

#### Профиль (`GET /users/me`) ![Профиль](img/get_profile.png)
Пример запроса:
```
curl -X 'GET' \
  'http://localhost:8000/users/me' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwiZXhwIjoxNzY3MTgzNTI1LCJpYXQiOjE3NjgzMjMxMjUsInJvbGUiOiJiYXNpY191c2VyIn0.1YoNt01zYLknHaDGLqrLep_BZsnXSDv3z5KeULYTY-k'
```
Пример ответа (200 OK):
``` json
{
  "first_name": "Evgeny",
  "last_name": "Anisimov",
  "patronymic": "Alexandrovish",
  "id": 6,
  "email": "anisimov@gmail.com",
  "is_active": true,
  "roles": ["basic_user"],
  "created_at": "2025-11-03T18:28:02.655821+03:00",
  "updated_at": "2025-11-03T18:28:02.655821+03:00"
}
```
