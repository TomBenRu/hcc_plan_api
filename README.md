# HCC Plan API

Ein webbasiertes Planungssystem für Klinikclown-Teams mit rollenbasiertem Zugriff, automatisierten Workflows und intelligenter Verfügbarkeitsplanung.

## 📋 Projektübersicht

HCC Plan API ist ein FastAPI-basiertes Webportal, das speziell für die Koordination von Klinikclown-Teams entwickelt wurde. Das System ermöglicht es Akteuren, ihre Verfügbarkeit für Planperioden anzugeben, während Dispatcher Teams verwalten und Supervisors die Planungsprozesse überwachen können.

### Hauptfeatures

- **🔐 Rollenbasierte Authentifizierung** - OAuth2/JWT mit vier Benutzerrollen
- **📅 Planperioden-Management** - Strukturierte Verfügbarkeitserfassung
- **👥 Team-Verwaltung** - Hierarchische Organisationsstruktur
- **📧 Automatisierte E-Mails** - Erinnerungen und Benachrichtigungen
- **⏰ Scheduler-Integration** - APScheduler für zeitgesteuerte Aufgaben
- **📱 Responsive Web-UI** - Moderne Benutzeroberfläche
- **🗄️ Multi-Database** - SQLite (Dev) / PostgreSQL (Prod)

### Zielgruppe

- **Actors (Klinikclowns)**: Eingabe ihrer Verfügbarkeit für Planperioden
- **Dispatcher**: Verwaltung von Teams und Koordination der Planung
- **Supervisors**: Überwachung von Planungsprozessen
- **Administratoren**: Projektverwaltung und Systemkonfiguration

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modernes Python Web-Framework
- **PonyORM** - Object-Relational Mapping
- **APScheduler** - Background Task Scheduling
- **Pydantic** - Data Validation & Settings Management
- **OAuth2/JWT** - Authentifizierung und Session Management

### Frontend
- **Jinja2** - Server-side Template Rendering
- **HTML/CSS/JavaScript** - Standard Web-Technologien
- **Responsive Design** - Mobile-optimierte UI

### Database
- **SQLite** - Development Database
- **PostgreSQL** - Production Database
- **Multi-Environment Support** - Flexible DB-Konfiguration

### Infrastructure
- **Uvicorn** - ASGI Server
- **Python 3.10+** - Moderne Python-Version
- **Virtual Environment** - Isolierte Dependencies

## 🚀 Installation & Setup

### Voraussetzungen
- Python 3.10 oder höher
- Git
- Virtueller Environment (empfohlen)

### Schritt-für-Schritt Installation

1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd hcc_plan_api
   ```

2. **Virtuelle Umgebung erstellen und aktivieren**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # oder
   source venv/bin/activate  # Linux/macOS
   ```

3. **Dependencies installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Umgebungskonfiguration erstellen**
   ```bash
   copy .env.example .env  # Windows
   # oder
   cp .env.example .env    # Linux/macOS
   ```

5. **Umgebungsvariablen konfigurieren**
   Bearbeiten Sie die `.env`-Datei mit Ihren spezifischen Einstellungen:
   ```env
   # Database
   provider=sqlite
   db_actors=databases/db_actors.sqlite
   
   # Security
   secret_key=your-secret-key-here
   algorithm=HS256
   access_token_expire_minutes=30
   
   # PostgreSQL (Production)
   provider_sql=postgresql
   host_sql=localhost
   user_sql=your_user
   database_sql=your_database
   password_sql=your_password
   
   # E-Mail Configuration
   send_address=your-email@example.com
   send_password=your-email-password
   post_ausg_server=smtp.gmail.com
   send_port=587
   
   # Admin Credentials
   supervisor_username=admin
   supervisor_password=secure_password
   ```

6. **Anwendung starten**
   ```bash
   python main.py
   ```

7. **Im Browser öffnen**
   - Hauptanwendung: http://127.0.0.1:8000
   - API-Dokumentation: http://127.0.0.1:8000/docs

## ⚙️ Konfiguration

### Umgebungsvariablen

Die Anwendung nutzt Pydantic Settings für die Konfigurationsverwaltung. Alle Einstellungen können über Umgebungsvariablen oder die `.env`-Datei konfiguriert werden.

#### Wichtige Konfigurationsoptionen:

| Variable | Beschreibung | Beispiel |
|----------|-------------|----------|
| `provider` | Datenbanktyp | `sqlite` / `postgresql` |
| `secret_key` | JWT Secret Key | `your-secret-key-here` |
| `db_actors` | SQLite Datenbankpfad | `databases/db_actors.sqlite` |
| `send_address` | E-Mail Absenderadresse | `notifications@example.com` |
| `supervisor_username` | Supervisor Login | `admin` |

### Datenbankeinrichtung

#### Development (SQLite)
Die SQLite-Datenbank wird automatisch beim ersten Start erstellt:
```bash
python main.py
# Datenbank wird unter databases/db_actors.sqlite erstellt
```

#### Production (PostgreSQL)
Für Produktionsumgebungen konfigurieren Sie PostgreSQL:
```env
provider_sql=postgresql
host_sql=your-postgres-host
user_sql=your-postgres-user
database_sql=your-database-name
password_sql=your-postgres-password
```

## 📚 Verwendung

### Benutzerrollen

Das System implementiert vier Hauptrollen mit unterschiedlichen Berechtigungen:

#### 🎭 Actors (Klinikclowns)
- Verfügbarkeit für Planperioden eingeben
- Eigene Termine und Zuweisungen einsehen
- Account-Einstellungen verwalten

#### 👨‍💼 Dispatcher
- Teams von Actors verwalten
- Planperioden erstellen und koordinieren
- Team-Übersichten und Statistiken

#### 👔 Supervisors
- Überblick über alle Planungsprozesse
- Monitoring von Team-Performance
- Eskalations-Management

#### 🔧 Administratoren
- Projektverwaltung und -konfiguration
- Benutzerverwaltung
- System-Einstellungen

### Typischer Workflow

1. **Administrator** erstellt Projekt und Teams
2. **Dispatcher** erstellt Planperioden für ihr Team
3. **Actors** geben ihre Verfügbarkeit für Planperioden ein
4. **System** versendet automatische Erinnerungen
5. **Dispatcher** koordiniert finale Planungen
6. **Supervisor** überwacht den gesamten Prozess

## 🏗️ Projektstruktur

```
hcc_plan_api/
├── main.py                    # FastAPI App Entry Point
├── settings.py                # Pydantic Settings
├── oauth2_authentication.py   # OAuth2/JWT Authentication
├── requirements.txt           # Python Dependencies
├── .env                       # Environment Configuration
├── README.md                  # Projekt-Dokumentation
│
├── routers/                   # API Endpoints
│   ├── index.py              # Landing Page Routes
│   ├── auth.py               # Authentication Routes
│   ├── actors.py             # Actor-specific Routes
│   ├── dispatcher.py         # Dispatcher Management
│   ├── supervisor.py         # Supervisor Routes
│   └── admin.py              # Admin Panel Routes
│
├── databases/                 # Data Layer
│   ├── database.py           # DB Connection & Init
│   ├── models.py             # PonyORM Entities
│   ├── schemas.py            # Pydantic Schemas
│   ├── services.py           # Business Logic
│   └── enums.py              # Enum Definitions
│
├── templates/                 # Jinja2 HTML Templates
│   ├── base_new.html         # Base Layout
│   ├── index_actor.html      # Actor Dashboard
│   ├── calendar_new.html     # Calendar Views
│   └── ...                   # Role-specific Templates
│
├── utilities/                 # Helper Modules
│   ├── scheduler.py          # APScheduler Config
│   ├── send_mail.py          # E-Mail System
│   └── utils.py              # General Utilities
│
└── static/                    # Static Web Assets
    └── (CSS, JavaScript, Images)
```

## 🔌 API-Dokumentation

### Automatische Dokumentation
FastAPI generiert automatisch interaktive API-Dokumentation:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Hauptendpunkte

#### Authentication
- `POST /auth/login` - Benutzer-Login
- `POST /auth/logout` - Benutzer-Logout
- `POST /auth/register` - Benutzer-Registrierung

#### Actors
- `GET /actors/plan-periods` - Verfügbare Planperioden anzeigen
- `POST /actors/plan-periods-handler` - Verfügbarkeit eingeben

#### Admin/Dispatcher/Supervisor
- `GET /admin/dashboard` - Admin-Dashboard
- `GET /dispatcher/teams` - Team-Übersicht
- `GET /supervisor/overview` - System-Übersicht

## 🧪 Testing

### Test-Ausführung
```bash
# Scheduler Tests
python test.py

# System-Integration Tests
python test_2.py

# Alternative Implementierungen
python test_3.py

# Pydantic Validation Tests
python test_pydantic.py
```

### Test-Struktur
- **test.py**: APScheduler und Job-Management Tests
- **test_2.py**: System-Integration und End-to-End Tests
- **test_3.py**: Alternative Feature-Implementierungen
- **test_pydantic.py**: Data Validation und Schema Tests

## 🚀 Deployment

### Development
```bash
# Lokaler Development Server
python main.py

# Mit Auto-Reload
uvicorn main:app --reload
```

### Production

#### Option 1: Uvicorn direkt
```bash
# Production Server
uvicorn main:app --host 0.0.0.0 --port 8000

# Mit Workers für bessere Performance
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Option 2: Reverse Proxy (empfohlen)
```nginx
# Nginx Configuration
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker (Optional)
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🛠️ Development

### Code-Style
Das Projekt folgt Python PEP 8-Standards:
- **Naming**: snake_case für Funktionen/Variablen, PascalCase für Klassen
- **Type Hints**: Vollständige Typisierung für bessere IDE-Unterstützung
- **Docstrings**: Deutsche Kommentare für komplexe Business Logic

### Pre-Commit Workflow
```bash
# Code formatieren (falls Tools installiert)
black .
isort .

# Tests ausführen
python test.py

# Anwendung testen
python main.py
```

### Database Migrations
```bash
# Development: Automatische Schema-Updates
# PonyORM generate_mapping(create_tables=True)

# Production: Manuelle Schema-Kontrolle
# Backup vor Schema-Änderungen erstellen
copy databases\db_actors.sqlite databases\backup\
```

## 🔧 Troubleshooting

### Häufige Probleme

#### Database Locked (SQLite)
```bash
# Problem: SQLite-Datenbank ist gesperrt
# Lösung: Alle Python-Prozesse beenden
taskkill /f /im python.exe
```

#### Port bereits belegt
```bash
# Problem: Port 8000 ist bereits belegt
# Lösung: Port-Nutzung prüfen
netstat -an | findstr 8000

# Alternativen Port verwenden
uvicorn main:app --port 8001
```

#### E-Mail-Versand funktioniert nicht
```bash
# Problem: SMTP-Konfiguration
# Lösung: .env-Datei prüfen
send_address=your-email@gmail.com
send_password=your-app-password
post_ausg_server=smtp.gmail.com
send_port=587
```

#### Template nicht gefunden
```bash
# Problem: Jinja2 findet Template nicht
# Lösung: Template-Pfad in main.py prüfen
templates = Jinja2Templates(directory='templates')
```

### Debugging

#### Logs analysieren
```bash
# FastAPI zeigt detaillierte Logs in der Konsole
python main.py

# Für mehr Details:
uvicorn main:app --log-level debug
```

#### Database debugging
```bash
# SQLite-Datenbank mit DBeaver öffnen:
# 1. DBeaver starten
# 2. Neue Verbindung → SQLite
# 3. Pfad: databases/db_actors.sqlite
```

## 📄 Lizenz

[Lizenz-Information hier einfügen]

## 🤝 Contributing

### Contribution Guidelines
1. **Fork** des Repositories erstellen
2. **Feature Branch** erstellen (`git checkout -b feature/amazing-feature`)
3. **Changes committen** (`git commit -m 'Add amazing feature'`)
4. **Branch pushen** (`git push origin feature/amazing-feature`)
5. **Pull Request** erstellen

### Code Review Checklist
- [ ] Authentication/Authorization korrekt implementiert
- [ ] Database Sessions ordentlich verwaltet (@db_session)
- [ ] Error Handling implementiert
- [ ] Template-Response korrekt strukturiert
- [ ] Keine hardcodierten Secrets
- [ ] Tests für neue Funktionalität

## 📞 Support

Bei Fragen oder Problemen:
1. **Issues** im GitHub-Repository erstellen
2. **Dokumentation** in diesem README konsultieren
3. **API-Dokumentation** unter `/docs` prüfen
4. **Logs** analysieren für Debugging-Informationen

---

**Entwickelt für Humor Hilft Heilen (HCC) - Klinikclown-Teams**

*Letzte Aktualisierung: August 2025*
