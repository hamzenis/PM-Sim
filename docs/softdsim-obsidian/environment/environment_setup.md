# Environment Setup Backend

## Environment Variables Overview

The environment variables are used to configure the backend and frontend services, including database connections and other settings. Below is a summary of the key environment variables used in the Docker deployment.

| Variable                     | Default                                              | Description                                  |
| ---------------------------- | ---------------------------------------------------- | -------------------------------------------- |
| `DATABASE_NAME`              | `sim`                                                | Name of database for the Django Backend      |
| `DATABASE_HOST`              | `127.0.0.1`                                          | Hostname of database for the Django Backend  |
| `DATABASE_PORT`              | `3306`                                               | Port for database for the Django Backend     |
| `DATABASE_USER`              | `demo`                                               | Username for database for the Django Backend |
| `DATABASE_PASS`              | `demo`                                               | Password for database for the Django Backend |
| `MONGO_NAME`                 | `sim`                                                | Name of MongoDB database                     |
| `MONGO_HOST`                 | `127.0.0.1`                                          | Hostname of MongoDB server                   |
| `MONGO_PORT`                 | `27017`                                              | Port for MongoDB server                      |
| `MONGO_USER`                 | `demo`                                               | Username for MongoDB database                |
| `MONGO_PASS`                 | `demo`                                               | Password for MongoDB database                |
| `LOGGING_LEVEL`              | `INFO`                                               | Logging level for Django backend             |
| `SECRET_KEY`                 | `ea2n+r$^@4px1c4gqim+l^m=@ew04hc-lupx^c&p(fy48)ma=0` | Secret key for Django application            |
| `MARIADB_ROOT_PASSWORD`      | `root`                                               | Root password for Database                   |
| `MARIADB_USER`               | `demo`                                               | Username for Database                        |
| `MARIADB_PASSWORD`           | `demo`                                               | Password for Database user                   |
| `MARIADB_DATABASE`           | `sim`                                                | Name of database                             |
| `MONGO_INITDB_ROOT_USERNAME` | `demo`                                               | Root username for MongoDB                    |
| `MONGO_INITDB_ROOT_PASSWORD` | `demo`                                               | Root password for MongoDB                    |
| `DJANGO_SUPERUSER_USERNAME`  | `admin`                                              | Username for Django superuser noinput        |
| `DJANGO_SUPERUSER_EMAIL`     | `admin@example.com`                                  | Email for Django superuser noinput           |
| `DJANGO_SUPERUSER_PASSWORD`  | `admin`                                              | Password for Django superuser noinput        |
|                              |                                                      |                                              |

## Quickstart
 Copy the `.env.template` file in `backend` to `.env` and fill in the required environment variables.


# Environment Setup Frontend

## Environment Variables Overview

The environment variables for the frontend service are used to configure the API endpoint and other settings. Below is a summary of the key environment variables used in the Docker deployment.

| Variable                | Default                  | Description                          |
| ----------------------- | ------------------------ | ------------------------------------ |
| `REACT_APP_DJANGO_HOST` | `http://localhost:8000` | URL of the Django backend API server |

## Quickstart

Copy the `.env.template` file in `frontend` to `.env` and fill in the required

