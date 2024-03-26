# Airport API Service

API service for tracking flights from airports across the whole globe.

## Installing using GitHub
Install PostgreSQL and create db

```shell
git clone https://github.com/DanSheremeta/airport-api.git
cd airport-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
set DJANGO_DEBUG=<True/False>
set DJANGO_SECRET_KEY=<your secret key>
set POSTGRES_DB=<your db name>
set POSTGRES_HOST=<your db hostname>
set POSTGRES_PORT=<your db port>
set POSTGRES_USER=<your db username>
set POSTGRES_PASSWORD=<your db user password>
python manage.py migrate
python manage.py runserver
```

## Run with docker

Docker should be installed

```shell
docker-compose build
docker-compose up
```

## Getting access

- create user via /api/user/register/
- get access token via /api/user/token/
