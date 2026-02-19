# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projekt-Überblick

HCC Plan API ist ein FastAPI-basiertes Webportal für Klinikclown-Teams ("Humor Hilft Heilen"). Es ermöglicht Actors (Klinikclowns), ihre Verfügbarkeit für Planperioden einzutragen, während Dispatcher Teams koordinieren und Supervisors den Überblick behalten.

## Befehle

```bash
# Anwendung starten (Development)
python main.py

# Mit Auto-Reload
uvicorn main:app --reload

# Debug-Logs
uvicorn main:app --log-level debug

# Abhängigkeiten installieren
pip install -r requirements.txt

# Testskripte ausführen
python test.py        # APScheduler & Job-Management
python test_2.py      # System-Integration
python test_pydantic.py  # Pydantic-Schema-Validierung
```

## Architektur

### Schichten

```
main.py              → FastAPI App-Einstiegspunkt, Router-Einbindung, Lifespan (DB + Scheduler)
settings.py          → Pydantic Settings (liest .env)
oauth2_authentication.py → JWT-Erstellung/-Prüfung, Cookie-basierte Auth-Helfer

routers/             → HTTP-Handler (geben Jinja2-TemplateResponse zurück oder leiten um)
databases/models.py  → PonyORM Entities (Datenbankschema)
databases/schemas.py → Pydantic v2 Schemas (Serialisierung/Validierung)
databases/services.py → Business-Logik (statische Methoden auf Klassen, alle mit @db_session)
databases/database.py → DB-Initialisierung (SQLite/PostgreSQL-Umschaltung)
utilities/scheduler.py → APScheduler BackgroundScheduler-Instanz
utilities/send_mail.py → E-Mail-Versand (async)
utilities/utils.py   → Passwort-Hashing, Hilfsfunktionen
```

### Datenmodell

Kernentitäten (PonyORM, `db_actors`):
- **Project** – Mandant/Organisation; hat genau einen `admin` (Person)
- **Person** – Benutzer; gehört zu einem Projekt; kann Dispatcher mehrerer Teams, Actor in einem Team oder Admin sein
- **Team** – hat einen Dispatcher (Person) und mehrere Actors (Persons)
- **PlanPeriod** – Planungszeitraum für ein Team; hat `start`, `end`, `deadline`; ein optionaler `APSchedulerJob`
- **Availables** – Verknüpfung Person↔PlanPeriod mit Notizen
- **AvailDay** – einzelner Verfügbarkeits-Tag (gehört zu `Availables`), mit `TimeOfDay` Enum

### Authentifizierung

- JWT-Token werden als HTTP-Cookie `hcc_plan_auth` gespeichert (nicht als Authorization-Header)
- Jede Route prüft das Cookie selbst: `get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.xxx)`
- Rollen: `supervisor` (aus `.env`), `admin`, `dispatcher`, `actor`, `google_calendar`
- Eine Person kann mehrere Rollen gleichzeitig haben (im JWT als Liste kodiert)
- Supervisor ist ein spezieller Hardcoded-Benutzer aus `.env` (kein DB-Eintrag)

### Datenbankzugriff (PonyORM)

- **Alle** Datenbankoperationen müssen innerhalb eines `@db_session` laufen
- Services-Klassen (`services.Person`, `services.Team`, …) kapseln alle DB-Zugriffe als statische Methoden
- `models.db_actors` ist die einzige Datenbankinstanz
- Umschaltung Dev/Prod in `databases/database.py` über `local = True/False`

### Umgebungsumschaltung

In `databases/database.py` steuern drei Flags die Verbindung:
```python
local = True           # True = SQLite (dev), False = PostgreSQL (prod)
server_remote_access = False
from_outside = False   # True = externer Zugriff auf Render.com PostgreSQL
```

Für die `.env`-Datei benötigte Variablen: siehe `settings.py` (`Settings`-Klasse).

### Scheduler

- `APScheduler BackgroundScheduler` läuft im Hintergrund
- Jobs werden in der Datenbank (`APSchedulerJob`-Entity) persistiert und beim Start geladen
- Zeitzone: `Europe/Berlin`
- Scheduler-Instanz ist ein Singleton in `utilities/scheduler.py`

### Router-Muster

Jeder Router:
1. Hat eine eigene `Jinja2Templates`-Instanz (`directory='templates'`)
2. Prüft das Auth-Cookie am Anfang jedes Handlers
3. Gibt entweder `TemplateResponse` oder `RedirectResponse` zurück
4. Nutzt `services.*`-Klassen für alle Datenbankoperationen

### Aktive Router

| Router | Prefix | Zweck |
|--------|--------|-------|
| `index.py` | `/` | Startseite, Login-Umleitung |
| `auth.py` | `/auth` | Login, Logout, Registrierung |
| `actors.py` | `/actors` | Verfügbarkeits-Eingabe für Actors |
| `dispatcher.py` | `/dispatcher` | Team- und Planperiodenverwaltung |
| `supervisor.py` | `/supervisor` | Überwachung |
| `admin.py` | `/admin` | Projektverwaltung, Benutzerverwaltung |

> `actors_new.py` ist auskommentiert (experimentelle Überarbeitung).
