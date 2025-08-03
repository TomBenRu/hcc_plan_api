# Projektstruktur - hcc_plan_api

## Root-Level Dateien
```
hcc_plan_api/
├── main.py                    # FastAPI App Entry Point mit Lifespan Management
├── settings.py                # Pydantic Settings für Konfiguration
├── oauth2_authentication.py   # OAuth2 und JWT Authentication Logic
├── requirements.txt           # Python Dependencies
├── .env                       # Umgebungsvariablen (sensible Daten)
├── .gitignore                 # Git Ignore Rules
├── test.py                    # Scheduler Tests
├── test_2.py                  # Additional System Tests  
├── test_3.py                  # Alternative Test Implementations
├── test_pydantic.py          # Pydantic Upgrade Tests
└── pydantic_upgrade.txt      # Pydantic Migration Notes
```

## Router-Architektur (API Endpoints)
```
routers/
├── __init__.py
├── index.py                  # Home Page und Landing Routes
├── auth.py                   # Authentication Routes (Login/Logout/Register)
├── actors.py                 # Actor-specific Routes (Verfügbarkeit eingeben)
├── actors_new.py            # Neue Actor-Features (in Entwicklung)
├── admin.py                 # Admin Panel Routes
├── supervisor.py            # Supervisor Management Routes
└── dispatcher.py            # Dispatcher Team Management Routes
```

## Datenbank-Layer
```
databases/
├── __init__.py
├── database.py              # Database Connection & Initialization
├── models.py                # PonyORM Entity Definitions
├── schemas.py               # Pydantic Schemas für API
├── services.py              # Business Logic Layer
├── enums.py                 # Enum Definitions (TimeOfDay, AuthorizationTypes)
├── enum_converter.py        # Enum Conversion Utilities
├── db_actors.sqlite         # SQLite Development Database
├── db_actors_.sqlite        # Backup/Alternative Database Files
└── db_actors__.sqlite       # Additional Database Versions
```

## Frontend-Templates
```
templates/
├── base_new.html            # Base Template Layout
├── index.html               # Main Landing Page
├── index_home.html          # Home Page für eingeloggte Benutzer
├── index_actor.html         # Actor Dashboard
├── index_new.html           # Neue UI-Version
├── login_modal_new.html     # Login Modal Dialog
├── calendar_new.html        # Calendar View Component
├── desktop_menu_new.html    # Desktop Navigation Menu
├── mobile_navigation_new.html # Mobile Navigation
├── account_settings_actor.html # Actor Account Settings
├── google_calendar.html     # Google Calendar Integration
├── period_dropdown_new.html # Period Selection Dropdown
├── period_icon_new.html     # Period Status Icons
├── period_notes_new.html    # Period Notes Component
├── period_response_new.html # Period Response Handling
├── notification_notes_new.html # Notification System
├── reset_password_new.html  # Password Reset Form
├── alert_invalid_credentials.html # Error Messages
├── alert_post_success.html  # Success Messages
├── test.html                # Template Testing
├── test_layout.html         # Layout Testing
├── test.css                 # Test Styles
└── icons/                   # Icon Assets
    └── .vs/                 # Visual Studio Files
```

## Utility-Module
```
utilities/
├── __init__.py
├── scheduler.py             # APScheduler Configuration & Management
├── send_mail.py             # E-Mail System (SMTP Integration)
└── utils.py                 # General Helper Functions
```

## Static Assets
```
static/
└── (CSS, JavaScript, Images)
    # Statische Web-Assets für Frontend
```

## Build & Output
```
output/
└── remote_gui/              # Compiled Application Output
    └── _internal/           # Internal Build Files
        └── _tk_data/        # Tkinter Data (falls GUI-Komponenten)
            └── images/      # Image Assets
                └── README   # Build Documentation

venv/                        # Virtual Environment
└── (Python Environment Files)
```

## Database Entity-Hierarchie

### Kern-Entitäten
- **Project**: Top-level Organisation (z.B. "Humor Hilft Heilen")
- **Person**: Benutzer mit verschiedenen Rollen
- **Team**: Gruppe von Actors unter einem Dispatcher
- **PlanPeriod**: Zeitraum für Verfügbarkeitsplanung

### Planungs-Entitäten
- **Availables**: Verfügbarkeit einer Person für eine Planperiode
- **AvailDay**: Spezifische Verfügbarkeitstage
- **APSchedulerJob**: Geplante Aufgaben/Erinnerungen

### Beziehungsstruktur
```
Project
├── admin (Person)
├── persons (Set[Person])
└── teams (via dispatcher.teams_of_dispatcher)

Team
├── dispatcher (Person)
├── actors (Set[Person])
└── plan_periods (Set[PlanPeriod])

Person
├── project (Project)
├── team_of_actor (Optional[Team])
├── teams_of_dispatcher (Set[Team])
├── project_of_admin (Optional[Project])
└── availabless (Set[Availables])
```

## Router-to-Role Mapping
- **index.py**: Öffentliche Startseite, allgemeine Navigation
- **auth.py**: Login, Logout, Registrierung für alle Rollen
- **actors.py**: Verfügbarkeit eingeben, Planperioden anzeigen
- **dispatcher.py**: Teams verwalten, Planungen koordinieren
- **supervisor.py**: Überwachung von Planungsprozessen
- **admin.py**: Projektverwaltung, Benutzerverwaltung

## Development vs Production Structure
```
Development:
├── SQLite Database (databases/db_actors.sqlite)
├── Local File-based Configuration (.env)
└── uvicorn --reload für Auto-Restart

Production:
├── PostgreSQL Database (via settings.provider_sql)
├── Environment Variables für Konfiguration
└── uvicorn ohne --reload für Stabilität
```

## Configuration Flow
```
settings.py
├── Liest .env-File
├── Fallback zu Environment Variables
├── Pydantic Validation
└── Bereitstellung für gesamte App
```

## Authentication Flow
```
oauth2_authentication.py
├── JWT Token Generation
├── Cookie-based Session Management
├── Role-based Access Control
└── Route Protection Middleware
```
