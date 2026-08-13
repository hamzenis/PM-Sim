# Entwicklungsworkflow

Für jedes geplante Feature, jeden Bug und jede Idee wird ein Issue angelegt und direkt dem Projekt-Board zugewiesen. Die Gesamtheit aller offenen Issues bildet das Backlog. Issues sollten so kleinteilig formuliert sein, dass sie in kurzer Zeit (einige Stunden bis maximal zwei Tage) abgeschlossen werden können. Größere Arbeiten sind in mehrere in sich abgeschlossene Issues aufzuteilen. Jedes Issue sollte eine kurze Beschreibung, Reproduktions‑/Umsetzungsschritte, Akzeptanzkriterien und Labels enthalten.

## Branches

Jedes Feature wird in einem eigenen Branch bearbeitet. Das Namensschema ist wie folgt:

```
type/issuenr-kurze-beschreibung
```

wobei ```issuenr``` die Ticketnummer des Issues ist und ```type``` eines von ```feature``` (Implementierung eines neuen Features), ```fix``` (Beheben eines Bugs/Fehlers), ```refactor``` (Umschreiben des Codes ohne neue Funktionalität) oder ```task``` (Alle anderen Arbeiten) ist.  Beispiel:

```
feature/127-Adding-api-delete-endpoint
task/123-Update-dependencies
refactor/45-Improve-code-structure
fix/78-Fix-login-bug
```

## Semantic Commit Messages


Die Commit-Messages sollten klar und prägnant sein und dem folgenden Schema folgen:

Format: `<type>: #IssueNumber <subject>`

Und optional eine längere Erklärung nach einer Leerzeile.

Wichtig ist das Symbol `#`, da dann der Commit automatisch durch GitHub zum Issue zugeteilt wird. Beispiel commit message: 

### Beispiel

```
feat: #73 add hat wobble
^--^  ^------------^
|     |
|     +-> Summary in present tense.
|
+-------> Type: chore, docs, feat, fix, refactor, style, or test.
```

### Typen Kategorien:

- `feat`: (new feature for the user, not a new feature for build script)
- `fix`: (bug fix for the user, not a fix to a build script)
- `docs`: (changes to the documentation)
- `style`: (formatting, missing semi colons, etc; no production code change)
- `refactor`: (refactoring production code, eg. renaming a variable)
- `test`: (adding missing tests, refactoring tests; no production code change)
- `chore`: (updating grunt tasks etc; no production code change)


## Pull Requests

Sobald ein Issue gelöst wurde, wird ein Pull Request zum Mergen des Branches in den *develop* Branch erstellt. Der PR muss dann mindestens ein Approval bekommen und die Tests bestehen, um dann gemergt zu werden.

## Dokumentation pflegen

- Übergreifende Orientierung gehört in die Root-[`README.md`](README.md). Backend-Themen gehören
  unter [`backend/docs/`](backend/docs/README.md), Frontend-Themen unter
  [`frontend/docs/`](frontend/docs/README.md). Die jeweiligen `README.md`-Dateien bleiben kurze
  Einstiegs- und Schnellstartseiten.
- Änderungen an Verhalten, API-Verträgen, Konfiguration, Datenmodell, Bedienabläufen oder Betrieb
  müssen die betroffenen Anleitungen im selben Pull Request aktualisieren. Gekoppelte Backend- und
  Frontend-Themen erhalten gegenseitige Links unter **Related documentation**.
- Befehle und Codebeispiele müssen aus dem angegebenen Arbeitsverzeichnis ausgeführt beziehungsweise
  gegen die aktuelle Schnittstelle geprüft werden. Beispiel-Payloads müssen validiert und relative
  Links vor dem Review auf erreichbare Ziele geprüft werden.
