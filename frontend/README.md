# Frontend

Diesen Abschnitt beschreibt die Frontend-Anwendung, die mit React 18 erstellt wurde.


## Requirements

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| **Node.js** | 18 LTS | CRA 5 supports Node ≥14; Node 18 is recommended |
| **npm**     | 8.x (bundled) | Package manager for scripts & dependencies |

> **Tipp:** Verwalte mehrere Node-Versionen mit [`nvm`](https://github.com/nvm-sh/nvm)

---

## Konfiguration

Erstelle eine `.env`-Datei im `frontend/`-Verzeichnis basierend auf `.env.template`.

```bash
# .env
REACT_APP_DJANGO_HOST=http://localhost:8000
```

---

## Installation

```bash
cd frontend
npm install --legacy-peer-deps
```

---

## npm Scripts

### Core scripts

| Script | Command |
|--------|---------|
| `start` | `react-scripts start` |
| `build` | `react-scripts build` |
| `test` | `react-scripts test` |
| `eject` | `react-scripts eject` |

---

## Development Workflow

1. **Starten** des Development-Servers:

   ```bash
   npm start
   ```

   Öffnet <http://localhost:3000>. 
   Änderungen im Verzeichnis `src/` führen zu einer sofortigen Aktualisierung.

2. **Tests kontinuierlich ausführen:**

   ```bash
   npm test
   ```

3. **Build** für den Prod erstellen:

   ```bash
   npm run build
   ```

   Optimierte Dateien werden im Verzeichnis `build/` abgelegt und können von jedem statischen Webserver wie Nginx oder Apache bereitgestellt werden.