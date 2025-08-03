# HCC Plan API - Projektübersicht

## Projektzweck
Das `hcc_plan_api` Projekt ist ein **webbasiertes Planungssystem** für Teams von Akteuren (Klinikclowns) mit automatisierter Verfügbarkeitsplanung. Die Anwendung ermöglicht:

- **Rollenbasierte Benutzerauthentifizierung** (Admin, Supervisor, Dispatcher, Actors)
- **Planperioden-Management** mit Verfügbarkeitseingabe
- **Automatisierte E-Mail-Benachrichtigungen** und Erinnerungen
- **Scheduler-basierte Aufgaben** für wiederkehrende Prozesse
- **Team- und Projektmanagement** mit hierarchischer Struktur
- **Webbasierte Kalenderansichten** für Planung
- **Multi-Database-Support** (SQLite/PostgreSQL)

## Hauptfunktionen
- **Planperioden-Verwaltung**: Akteure können ihre Verfügbarkeit für bestimmte Zeiträume eingeben
- **Team-Management**: Dispatcher verwalten Teams von Akteuren innerhalb von Projekten
- **Automatisierte Workflows**: APScheduler für zeitgesteuerte Erinnerungen und Benachrichtigungen
- **E-Mail-Integration**: Automatischer Versand von Bestätigungen und Erinnerungen
- **Responsive Web-UI**: Modern gestaltete Weboberfläche mit Jinja2-Templates
- **Account-Management**: Benutzerregistrierung, Passwort-Reset, Profilverwaltung

## Projektkontext
Dieses Projekt ist Teil der HCC (Humor Hilft Heilen) Planungstools-Familie von Thomas. Es ergänzt:
- `hcc_plan_db_playground` - Desktop-Anwendung mit komplexer SAT-Solver-Planung
- `appointment_plan_api_cl` - Einfache Terminplanungs-Webapplikation

`hcc_plan_api` stellt die Brücke zwischen einfacher Terminplanung und komplexer Optimierung dar, mit Fokus auf Verfügbarkeitserfassung und Teamkoordination.

## Zielgruppe
- **Actors (Klinikclowns)**: Eingabe ihrer Verfügbarkeit für Planperioden
- **Dispatcher**: Verwaltung von Teams und Koordination der Planung
- **Supervisors**: Überwachung von Planungsprozessen
- **Administratoren**: Projektverwaltung und Systemkonfiguration

## System-Architektur
- **Web-Frontend**: HTML/CSS/JavaScript mit Jinja2-Templates
- **API-Backend**: FastAPI mit rollenbasierter Autorisierung
- **Datenbank**: PonyORM mit SQLite (Dev) / PostgreSQL (Prod)
- **Scheduler**: APScheduler für automatisierte Aufgaben
- **E-Mail-System**: SMTP-Integration für Benachrichtigungen
