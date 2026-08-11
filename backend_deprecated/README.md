# Backend

> Achtung: In dieser Readme werden alle python Aufrufe mit dem Befehl `python` beschreiben. Je nach der Python Konfiguration auf deinem System muss dies nicht so sein, häufig verwenden MacOS oder Linux Systeme den Alias `python3`. Es wird empfohlen eine virtuelle Umgebung zu nutzen, um Versionskonflikte zu vermeiden.

## Python

Eine Installation von [Python 3.10](https://www.python.org/downloads/) ist notwendig. Falls auf dem System verschiedene Python Projekte vorhanden sind, ist es sinnvoll für das *SoftDSim* Projekt ein eigenes Python Environment (siehe [virtualenv](https://pypi.org/project/virtualenv/) oder [venv](https://docs.python.org/3/library/venv.html)) anzulegen.


```bash
cd backend
virtualenv .venv --python=python3.10
source .venv/bin/activate
```


## Requirements installieren

Die nötigen Pythonabhängigkeiten bzw. zu installierende Bibliotheken befinden sich als `requirements.txt` im *backend* Verzeichnis des Projekts.

Die Installation aller benötigter Bibliotheken geschieht mittels `pip` über den Befehl:

```bash
pip install -r requirements.txt
```

Eines der Requirements ist `mysqlclient`, dieses benötigt einen mysql-client auf dem lokalen System. 
[Auf der pypi Seite für mysqlclient](https://pypi.org/project/mysqlclient/) findet sich dazu eine Erklärung für MacOS, Linux und Windows Systeme.


## Datenbank

Die Datenbank, die von der Webanwendung genutzt wird, ist die SQL Datenbank [mariaDB](https://mariadb.org/). Die Datenbank muss nicht zwingendermaßen auf demselben Server wie das Backend laufen. Für die Entwicklung ist es erforderlich, dass Entwickler eine eigene Datenbank anbinden. Es wird empfohlen die Datenbank mittels Docker zu betreiben.

### Docker

Siehe die Dokumentation zur [Docker-Installation](https://softdsim-docs.readthedocs.io/en/latest/documentation/docker_deployment.html) für eine einfache Installation der Datenbank mit Docker. Diese ist die empfohlene Variante, da sie am einfachsten zu installieren ist und keine weiteren Abhängigkeiten benötigt.

#### TLDR: Docker-Compose

Um die Datenbank mit Docker Compose schnell zu starten, kann Docker Compose genutzt werden. Dazu führe im *root* Verzeichnis des Projekts den Befehl aus:

```bash
docker compose -f docker/docker-compose.yml up -d
```

## Projekt Konfiguration

Die Environment Variablen enthalten wichtige Informationen über die lokale Konfiguration. Sie werden in der Datei `.env` im *root* Verzeichnis des Projekts definiert.
Siehe dafür die `.env.template` Datei im *backend* Verzeichnis als Vorlage. Weitere Informationen zu der Environment Konfiguration sind in der [Dokumentation](https://softdsim-docs.readthedocs.io/) zu finden.


## Erstes Starten der Webanwendung

Zum Starten der Anwendung wird der Befehl

```bash
python manage.py runserver
```

Dann wird die Webanwendung lokal gehostet und ist unter http://127.0.0.1:8000/ zu erreichen.

Die Adresse kann im Browser geöffnet werden, dort wird nun die Login-Seite angezeigt. Um einen ersten (Super-)Nutzer zu erstellen, muss zurück in das Terminal (Eingabeaufforderung) gewechselt werden. Vor dem ersten Gebrauch muss die Datenbank durch die Django Migrations initialisiert werden. Dies geschieht mit dem Befehl:

```bash
python manage.py migrate
```

Danach kann ein Superuser (Nutzer mit Admin-Rechten) mit dem Befehl

```bash
python manage.py createsuperuser --noinput
```

erstellt werden. Die notwendigen Informationen wie Username, Email und Passwort müssen vorher in der `.env` Datei definiert werden.

```bash
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin
```

Der definierte Username und das Passwort können zur Anmeldung auf der Loginseite der Webapplikation genutzt werden.