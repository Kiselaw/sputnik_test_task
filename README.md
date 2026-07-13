# sputnik_test_task

## Что изменено

Backend разделен на две главные сущности:

- `backend` запускает FastAPI API.
- `backend-worker` запускает Celery worker и Flower.

Архитектура тут, скорее, модульный монолит, а не микросервисы, поскольку API и worker остаются в одной кодовой базе и используют одну БД (которая в большей степени и является причиной выбора архитектуры), но их жизненный цикл разделен, равно как зависимости и Dockerfile-ы разделены.
Чистые микросервисы были бы, пожалуй, преждевременным усложнением (тем не менее основа под это заложена). 

Основные решения (в том числе по оптимизации кода):

- HTTP-слой вынесен в `src/app/api`, бизнес-операции - в services/repositories, выделана и работа с базой (создание сессий `src/db/session.py`).
- Добавлен паттерн `UnitOfWork`, в первую очередь это было сделано для атомарного удаления файла и связанного алерта (во всяком случае в рамках работы с БД).
- Celery worker и задачи вынесены в `src/worker`.
- Создан общий конфиг, лежит здесь -  `src/core/config.py`.
- Изменена логика запуска асинхронного кода в рамках Celery worker - теперь создается один event loop на process через `worker_process_init`.
- Celery задача теперь одна, я посчитал, что получение метадаты и и проверка на угрозы не столь тяжелые операции чтобы их отдельно выделять в задачу, поэтому они теперь является этапами в рамках одной общей задачи.
- **ОПТИМИЗАЦИЯ:** Загрузка файлов идет через разбиение на чанки, без чтения всего файла в память.
- **ОПТИМИЗАЦИЯ:** То же самое касается и получения метадаты, но помимо этого блокирующая запись на диск выносится в `asyncio.to_thread`.
- UUID4 заменен на UUID7.
- Миграции запускаются автоматически в app entrypoint.
- Добавлен Flower для отслеживания Celery задач, доступ к нему закрыт basic auth.
- Добавлено разделение зависимостей, в том числе dev групп (`ruff`, `pytest`, `httpx`).

**ВАЖНО:** хранилище файлов оставил именно как было изначально - то есть через mount на папку на хосте.
Но в целом без проблем можно добавить и отдельный volume для этих целей. Названия compose файлов и env тоже специально оставил такими, как были.

**Что еще следовало бы сделать**, но в рамках тестового задания посчитал лишним: 

1) Полноценное и продуманное логирование
2) Подробная документация для API в Swagger формате.

Касаемо frontend:

Не стал трогать код. Я понимаю, что там, условно, все запихано в один компонент, а значит он подлежит разбиению, но у меня было бы больше шансов сломать уже то, что есть :)
Мог бы сделать с нейронкой, но не смогу полноценно объяснить и оценить корректность решений (ибо все-таки понадобится время поразбираться), а не понимать - не люблю. 


## Запуск

Создать `.env.dev` в корне проекта (ниже указаны необходимые переменные).

Запустить проект:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Миграции применять вручную не нужно: app entrypoint выполняет `alembic upgrade head`, если `RUN_MIGRATIONS=1`.

Адреса:

- Frontend: `http://localhost:3000/test`
- Backend docs: `http://localhost:8000/docs`
- Flower: `http://localhost:5555`

## Обязательные переменные окружения

Для dev compose должны быть заданы:

```env
# Postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=test
POSTGRES_HOST=backend-db
PGPORT=5433

# Celery / Redis
REDIS_URL=redis://backend-redis:6379/0
CELERY_BROKER_URL=redis://backend-redis:6379/0
CELERY_RESULT_BACKEND=redis://backend-redis:6379/0
FILE_PROCESSING_QUEUE=file-processing
PROCESS_UPLOADED_FILE_TASK_NAME=process_uploaded_file
CELERY_LOGLEVEL=info
UPLOAD_CHUNK_SIZE_BYTES=1048576
MAX_SAFE_FILE_SIZE_BYTES=10485760
SUSPICIOUS_FILE_EXTENSIONS=[".exe",".bat",".cmd",".sh",".js"]

# Celery Flower
FLOWER_HOST=0.0.0.0
FLOWER_PORT=5555
FLOWER_USER=admin
FLOWER_PASSWORD=admin
```

Опционально можно добавить следующие переменные:

```env
UPLOAD_CHUNK_SIZE_BYTES=1048576
MAX_SAFE_FILE_SIZE_BYTES=10485760
SUSPICIOUS_FILE_EXTENSIONS=[".exe",".bat",".cmd",".sh",".js"]
```

## Проверки бэкенда

Перед локальными проверками установить зависимости:

```bash
cd backend
uv sync --all-groups
```

Тесты API эндпоинтов:

```bash
pytest
```

Линтер:

```bash
ruff check src migrations tests
```

Валидация Docker compose:

```bash
docker compose -f docker-compose.dev.yml config --quiet
```
