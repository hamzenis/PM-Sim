# softDsim

IT Project Management Simulation Web Application

[Dokumentation](https://softdsim-docs.readthedocs.io)

## Abstract

Die SoftDSim ist eine Django-basierte Web-Anwendung zur Simulation von Projektmanagement-Szenarios für den Einsatz im Modul Project Management an der [Frankfurt University of Applied Sciences](https://www.frankfurt-university.de/). Dozenten können innerhalb der Web-Anwendung Szenarios mit belieben Inhalten definieren, welche dann von Studierenden simuliert werden. Die Studierenden nehmen dabei die Rolle eines Projektmanagers ein und müssen verschiedene Entscheidungen treffen. Beispielhaft genannte Entscheidungen sind _Projektmanagementmethode_, _Anzahl und Erfahrungsniveau der Teammitglieder_ oder _Anzahl der Meetings_. Alle Simulationen werden in einer gemeinsamen Datenbank gespeichert. Diese kann vom Dozenten eingesehen werden, sodass die Leistungen der Studierenden evaluiert werden kann.

## Schnellstart

Das Projekt besteht aus mehreren Komponenten (Frontend, Backend und Datenbank), die separat gestartet werden müssen.

### Voraussetzungen

- Docker
- Python 3.10+
- Node.js und npm

### Starten der Anwendung

In diesem Abschnitt wird beschrieben, wie die Anwendung lokal gestartet werden kann. Es wird davon ausgegangen, dass die Voraussetzungen erfüllt sind und die Intialisierungsschritte durchgeführt wurden. Für mehr Informationen siehe dazu die Dokumentation.

Starten der **Datenbank**:

```bash
docker compose -f docker/docker-compose.yml up -d
```

Starten des **Backends**:

```bash
cd backend
python manage.py runserver
```

Starten des **Frontends**:

```bash
cd frontend
npm start
```


## Weitere Informationen

### Backend & Datenbank

Siehe dazu die [README-Datei](backend/README.md) im Ordner `backend/`.

### Frontend

Siehe dazu die [README-Datei](frontend/README.md) im Ordner `frontend/`.
