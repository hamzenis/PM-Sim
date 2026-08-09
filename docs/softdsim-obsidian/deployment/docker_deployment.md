# Database Container

This guide explains how to run the SoftDsim database services using Docker

---

## Overview

The stack contains four services orchestrated by **Docker Compose**:

| Service                | Image                 | Purpose             | Host Port |
| ---------------------- | --------------------- | ------------------- | --------- |
| `maria_application_db` | `mariadb:mariadb:11.8-noble`     | Relational database | **3306**  |
| `mongo_template_db`    | `mongo:8.2.2-noble`              | Scenario Studio       | **27017** |

Data for MariaDB is persisted in the named volume **`maria_store`** so that it
survives container rebuilds.
Same for MongoDB with volume **`mongo_store`** and **`mongo_config`**.

---

## Prerequisites

-   Docker Engine & Docker Compose v2  
    (`docker compose version` → v2.x)
-   Filled Environment Variable. [See Environment Setup.](environment_setup.md)

---

## Starting the database container

From the project root directory

```console
docker compose -f docker/docker-compose.yml up -d
```

Shut everything down (and delete the database volume) with:

```console
# Stop and remove containers, networks, and volumes
docker compose -f docker/docker-compose.yml down -v

# Remove dangling volumes (optional)
docker volume prune

# Only stop containers (keep volumes)
docker compose -f docker/docker-compose.yml down
```


## Clean‑Up

```console
docker compose down -v       # stop containers and delete maria_store
docker volume prune          # remove dangling volumes (optional)
```

---

## Production Notes

-   Replace the Django dev server with **Gunicorn** or **Uvicorn**.
-   Add HTTPS termination (Traefik, Caddy, Nginx) in front of the stack.
-   Mount an external volume or managed database for MariaDB instead of the local
    `maria_store`.
