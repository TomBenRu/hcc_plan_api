# Tech Stack - hcc_plan_api

## Web-Framework
- **FastAPI** - Modernes Python Web-Framework für API-Entwicklung
- **Uvicorn** - ASGI Server für FastAPI-Anwendungen
- **Python** - Hauptprogrammiersprache (unterstützt 3.10, 3.11, 3.12)

## Frontend-Technologien
- **Jinja2** - Template-Engine für HTML-Rendering
- **HTML/CSS/JavaScript** - Standard Web-Technologien
- **Responsive Design** - Mobile-optimierte Benutzeroberfläche
- **Static Files** - CSS, JavaScript, Icons über FastAPI StaticFiles

## Datenbank & ORM
- **PonyORM** - Object-Relational Mapping für Python
- **SQLite** - Entwicklungsdatenbank (databases/db_actors.sqlite)
- **PostgreSQL** - Produktionsdatenbank (über settings.provider_sql)
- **Multi-Database Support** - Flexibler Wechsel zwischen DB-Systemen

## Authentifizierung & Sicherheit
- **OAuth2** - Authentifizierungsprotokoll
- **JWT Tokens** - Session-Management mit Access Tokens
- **Cookie-based Auth** - Web-Frontend-Authentifizierung
- **Role-based Access Control** - Granulare Berechtigungen nach Rollen
- **Password Hashing** - Sichere Passwort-Speicherung

## Konfiguration & Settings
- **Pydantic Settings** - Type-safe Konfigurationsverwaltung
- **.env Files** - Umgebungsvariablen für sensible Daten
- **BaseSettings** - Hierarchische Konfiguration mit Fallbacks

## Scheduler & Automation
- **APScheduler** - Background-Task-Scheduling
- **BackgroundScheduler** - Persistente Jobs über App-Restarts
- **pytz** - Timezone-Management (Europe/Berlin)
- **Job Persistence** - Jobs werden in der Datenbank gespeichert

## E-Mail-System
- **SMTP Integration** - Automatischer E-Mail-Versand
- **Konfigurierbare Mail-Server** - Über settings.send_address, send_password
- **Template-basierte E-Mails** - HTML/Text E-Mail-Templates

## Data Validation & Serialization
- **Pydantic** - Data Validation und API-Schema-Definition
- **Type Hints** - Vollständige Typisierung für bessere IDE-Unterstützung
- **Enum Support** - Strukturierte Datentypen für Status und Konfiguration

## Development Tools
- **requirements.txt** - Dependency Management
- **Virtual Environment** - Isolierte Python-Umgebung (venv/)
- **Multiple Python Versions** - Unterstützung für 3.10, 3.11, 3.12
- **Test Files** - Verschiedene Test-Implementierungen

## Architektur-Pattern
- **MVC Pattern** - Model (databases/), View (templates/), Controller (routers/)
- **Service Layer** - Business Logic in databases/services.py
- **Repository Pattern** - Datenzugriff über PonyORM-Entities
- **Middleware Pattern** - Authentifizierung und Error-Handling

## Deployment & Infrastructure
- **Multi-Environment Support** - Dev (SQLite) / Prod (PostgreSQL)
- **Static File Serving** - Integrierte Static-File-Verwaltung
- **Database Migrations** - Automatische Schema-Updates via PonyORM
- **Environment-based Configuration** - Flexible Deployment-Konfiguration
