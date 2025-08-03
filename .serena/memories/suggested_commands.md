# Wichtige Commands - hcc_plan_api

## Entwicklungsserver starten
```bash
# Hauptanwendung starten
python main.py

# Alternative mit Uvicorn direkt
uvicorn main:app --reload

# Mit spezifischem Host und Port
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Dependency Management
```bash
# Virtuelle Umgebung aktivieren (Windows)
venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Neue Abhängigkeit hinzufügen
pip install <package-name>
pip freeze > requirements.txt

# Abhängigkeiten aktualisieren
pip install --upgrade -r requirements.txt
```

## Datenbank-Operationen
```bash
# Datenbankschema überprüfen
# SQLite-Datei: databases/db_actors.sqlite
# Mit DBeaver oder ähnlichem Tool öffnen

# Datenbank-Migration (automatisch beim App-Start)
# PonyORM generate_mapping(create_tables=True) wird in database.py ausgeführt

# Backup der SQLite-Datenbank erstellen
copy databases\db_actors.sqlite databases\db_actors_backup.sqlite
```

## Testing
```bash
# Test-Dateien ausführen
python test.py
python test_2.py
python test_3.py
python test_pydantic.py

# Spezifische Tests für verschiedene Komponenten
# test.py - Scheduler-Tests
# test_2.py - Weitere System-Tests
# test_3.py - Alternative Implementierungen
# test_pydantic.py - Pydantic-Upgrade-Tests
```

## Konfiguration & Setup
```bash
# .env-Datei bearbeiten (sensible Daten)
notepad .env

# Settings überprüfen
python -c "from settings import settings; print(settings)"

# Umgebungsvariablen setzen (Windows)
set DATABASE_URL=postgresql://user:password@localhost/dbname
set SECRET_KEY=your-secret-key-here
```

## Scheduler-Management
```bash
# APScheduler-Jobs über Web-Interface verwalten
# (wenn implementiert in der Anwendung)

# Scheduler-Status prüfen
# Logs in der Konsole beim App-Start überprüfen
```

## Development Workflow
```bash
# 1. Virtuelle Umgebung aktivieren
venv\Scripts\activate

# 2. Abhängigkeiten aktualisieren
pip install -r requirements.txt

# 3. .env-Datei konfigurieren
# (falls noch nicht vorhanden)

# 4. Entwicklungsserver starten
python main.py

# 5. In Browser öffnen
# http://127.0.0.1:8000
```

## Deployment Commands
```bash
# Produktionsserver starten
uvicorn main:app --host 0.0.0.0 --port 8000

# Mit PostgreSQL-Datenbank
set provider_sql=postgresql
set host_sql=your-host
set database_sql=your-database
set user_sql=your-user
set password_sql=your-password
uvicorn main:app --host 0.0.0.0 --port 8000

# Background-Server (Windows Service oder nohup-Äquivalent)
# Über Task Scheduler oder externe Service-Management-Tools
```

## Git-Workflow (Windows)
```bash
# Repository-Status prüfen
git status

# Änderungen hinzufügen
git add .

# Commit mit Nachricht
git commit -m "feat: neue Funktionalität hinzugefügt"

# Remote-Repository aktualisieren
git push origin main

# Änderungen vom Remote-Repository holen
git pull origin main
```

## Debugging & Logs
```bash
# App mit Debug-Informationen starten
# (FastAPI zeigt automatisch detaillierte Logs)

# SQLite-Datenbank-Debugging
# Öffne databases/db_actors.sqlite in DBeaver:
# 1. Neuer DB-Connection erstellen
# 2. SQLite auswählen
# 3. Pfad zur .sqlite-Datei angeben

# E-Mail-System testen
# Über Web-Interface oder direkt:
python -c "from utilities.send_mail import send_confirmed_avail_days; print('Testing email...')"
```

## System-spezifische Commands (Windows)
```bash
# Projektverzeichnis navigieren
cd C:\Users\tombe\PycharmProjects\hcc_plan_api

# Python-Version prüfen
python --version

# Ports prüfen (ob 8000 belegt)
netstat -an | findstr 8000

# Prozesse beenden (falls nötig)
taskkill /f /im python.exe

# Virtuelle Umgebung erstellen (falls nicht vorhanden)
python -m venv venv

# Requirements-Datei neu generieren
pip freeze > requirements.txt
```

## API-Testing
```bash
# FastAPI automatische Dokumentation
# Browser: http://127.0.0.1:8000/docs

# Alternative API-Dokumentation
# Browser: http://127.0.0.1:8000/redoc

# Direct API-Calls mit curl (Windows)
curl -X GET "http://127.0.0.1:8000/actors/plan-periods" -H "accept: application/json"
```

## Maintenance Commands
```bash
# Log-Dateien bereinigen (falls vorhanden)
del *.log

# Temporäre Dateien bereinigen
del /s __pycache__
del /s *.pyc

# Datenbank-Backup erstellen
xcopy databases\db_actors.sqlite backup\ /Y

# Konfiguration zurücksetzen
copy .env.example .env
```
