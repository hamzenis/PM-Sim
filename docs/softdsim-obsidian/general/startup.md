# Starting softDsim

This document explains how to get softDsim running locally for development and how to start it.

---

## Prerequisites

- Python 3.10+ used for the Django API
- Node.js 18 and npm for the React frontend in `frontend/`
- Docker and Docker Compose


## Starting

### Environment Setup

Fill the environment variables as needed. Refer to the `Environment variables` document for more details.
For quick setup, you can copy the example `.env.template` and rename it to `.env` in the `backend/` directory and adjust values there.

### Database with Docker

This uses the included Docker Compose configuration in `docker/docker-compose.yml` to run the database.

From the repository root start the database container:

```bash
docker compose -f docker/docker-compose.yml up -d
```

>Tip: Use the `docker compose` command rather than the legacy `docker-compose` binary.

### Backend

This section describes how to run the backend and frontend.

1. Create and activate a virtual environment (recommended inside `backend/` directory):

> Attention: In this Documentation all python calls are described with the command `python`. Depending on the Python configuration on your system this may not be the case, frequently MacOS or Linux systems use the alias `python3`. It is recommended to use a virtual environment to avoid version conflicts.

```bash
cd backend
virtualenv .venv --python=python3.10
source .venv/bin/activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Prepare the database and create a superuser:

The database migrations need to be applied before using the application for the first time:

```bash
python manage.py migrate
```

To create an initial superuser for accessing the admin interface, run:

```bash
python manage.py createsuperuser --noinput
```

4. Start the development server:

```bash
python manage.py runserver
```

### Frontend

This section describes how to run the frontend.

1. Install Node.js dependencies and start the frontend dev server:
    Please refer to the [node.js official website](https://nodejs.org/en/download) for the current installation instructions.
> Recommended Node.js version is current LTS (v24.12.0 as of December 2025)

Here is a small guide for installing node.

On MacOS and Linux systems, you can use the version manager `nvm`:
```bash
# Download and install nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# in lieu of restarting the shell
\. "$HOME/.nvm/nvm.sh"

# Download and install Node.js:
nvm install 24

# Verify the Node.js version:
node -v # Should print "v24.12.0".

# Verify npm version:
npm -v # Should print "11.6.2".
```

On Windows you can use the [chocolatey package manager](https://chocolatey.org/install):
```bash
# Download and install Chocolatey:
powershell -c "irm https://community.chocolatey.org/install.ps1|iex"

# Download and install Node.js:
choco install nodejs --version="24.12.0"

# Verify the Node.js version:
node -v # Should print "v24.12.0".

# Verify npm version:
npm -v # Should print "11.6.2".
```

2. After installing Node.js, navigate to the `frontend/` directory, install dependencies, and start the frontend dev server:

```bash
cd frontend
npm install
npm start
```

The frontend's dev server typically runs on port 3000 and proxies API calls to the backend during development (see `frontend/package.json` or `frontend/README.md` for details).


## Database and migrations

- To create and apply migrations for model changes, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Running tests

TODO: WIP - to be documented fully
Backend (pytest):

```bash
cd backend
pytest
```


## Common troubleshooting

- Database connection refused:
	- Ensure MariaDB is running 
	- If using Docker, ensure the DB container is running properly 

- Port already in use:
	- Change port or stop the process using the port.
    - Make sure no other instance of the MariaDB is running on the same port locally as the Docker container.
    - If Django, then stop the process and restart it after a short wait



## Production notes and security

- Never run production with `DEBUG=True` in Django settings (backend/softDsim/settings.py)
- Provide a strong `SECRET_KEY` in production and keep it secret
- Use Gunicorn or another production-ready WSGI server for Django in production
