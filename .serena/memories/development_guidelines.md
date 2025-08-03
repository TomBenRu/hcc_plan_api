# Entwicklungsrichtlinien - hcc_plan_api

## Allgemeine Prinzipien

### Thomas' Präferenzen
⚠️ **WICHTIG**: Thomas bevorzugt **Absprache vor strukturellen Änderungen** an Architekturkomponenten
- Vor größeren Refactorings oder Architektur-Änderungen Rücksprache halten
- Bestehende Patterns und bewährte Strukturen respektieren
- Keine Breaking Changes ohne ausdrückliche Zustimmung
- Schrittweise Verbesserungen bevorzugt gegenüber radikalen Umbauten

### Code-Qualität
- **Konsistenz**: Bestehende Code-Patterns beibehalten
- **Lesbarkeit**: Code soll selbsterklärend sein
- **Maintainability**: Einfache, wartbare Lösungen bevorzugen
- **Documentation**: Deutsche Kommentare für komplexe Business Logic

## Authentifizierung & Sicherheit

### Role-based Development
```python
# Standard-Pattern für Router-Protection
@router.get('/endpoint')
def protected_endpoint(request: Request):
    try:
        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    except Exception as e:
        # Error Handling - Redirect oder Template-Response
        return RedirectResponse(request.url_for('home'), status_code=status.HTTP_303_SEE_OTHER)
    
    # Geschützte Logik hier
```

### Authorization Types
- **AuthorizationTypes.actor**: Für Akteure (Verfügbarkeit eingeben)
- **AuthorizationTypes.dispatcher**: Für Team-Management
- **AuthorizationTypes.supervisor**: Für Überwachung
- **AuthorizationTypes.admin**: Für System-Administration

## Datenbank-Entwicklung

### PonyORM Best Practices
- **@db_session**: Für alle Datenbankoperationen verwenden
- **UUID Primary Keys**: Standard für alle Entitäten
- **Zeitstempel**: `created_at`, `last_modified` mit automatischen Defaults
- **Composite Keys**: Für Business-relevante Eindeutigkeit

### Schema-Änderungen
```python
# Before-Hooks für Business Logic
def before_update(self):
    # Automatisches last_modified Update
    self.last_modified = datetime.utcnow()
    
    # Business Logic bei Änderungen
    if self.team_of_actor != old_value:
        # Cleanup-Logik
```

### Database Migration
- **Development**: Automatisches `create_tables=True`
- **Production**: Manuelle Schema-Updates nach Testing
- **Backup**: Vor Schema-Änderungen immer Backup erstellen

## Frontend-Entwicklung

### Template-Response Pattern
```python
return templates.TemplateResponse('template_name.html',
                                 context={
                                     'request': request,
                                     'user': user,
                                     'data': data,
                                     'additional_context': value
                                 })
```

### Error Handling in Templates
- **Invalid Credentials**: `alert_invalid_credentials.html`
- **Success Messages**: `alert_post_success.html`
- **Graceful Degradation**: Fallback-Templates für Fehler

### Template Organization
- **Base Templates**: `base_new.html` für Layout-Konsistenz
- **Component Templates**: Wiederverwendbare UI-Komponenten
- **Role-specific**: Templates nach Benutzerrollen organisiert

## Scheduler-Entwicklung

### APScheduler Integration
```python
# Job Registration Pattern
scheduler.add_job(
    func=job_function,
    trigger='cron',
    id='unique_job_id',
    **job_parameters
)

# Job Persistence
# Jobs werden in APSchedulerJob-Entity gespeichert
```

### Job Management
- **Startup Loading**: Jobs aus Datenbank beim App-Start laden
- **Dynamic Jobs**: Zur Laufzeit Jobs hinzufügen/entfernen
- **Error Handling**: Graceful Failure bei Job-Execution

## E-Mail-System

### Mail Integration
```python
# Standard E-Mail-Sending Pattern
from utilities.send_mail import send_confirmed_avail_days

# Konfiguration über settings.py
send_address = settings.send_address
send_password = settings.send_password
```

### E-Mail Best Practices
- **Template-based**: HTML/Text E-Mail-Templates
- **Async Sending**: Nicht-blockierende E-Mail-Versendung
- **Error Handling**: Retry-Mechanismen für Failed Sends

## Testing-Richtlinien

### Test-Struktur
- **test.py**: Scheduler-Tests
- **test_2.py**: System-Integration-Tests
- **test_3.py**: Alternative Implementierungen
- **test_pydantic.py**: Data Validation Tests

### Test-Isolation
- **Separate Databases**: test_jobs.sqlite etc.
- **Mock External Services**: E-Mail, External APIs
- **Clean State**: Tests sollten unabhängig laufen

## Configuration Management

### Settings Pattern
```python
# Hierarchische Konfiguration
try:
    settings = Settings()  # Aus Environment
except Exception as e:
    settings = Settings(_env_file='.env')  # Aus .env-File
```

### Environment Variables
- **Development**: .env-File für lokale Entwicklung
- **Production**: Environment Variables für Deployment
- **Sensitive Data**: Niemals in Git committen

## Error Handling

### Exception Strategy
- **User-Friendly**: Template-basierte Error-Pages
- **Logging**: Detaillierte Logs für Debugging
- **Graceful Degradation**: App läuft weiter bei Teilfehlern

### Common Error Patterns
```python
try:
    # Critical Operation
    result = critical_operation()
except SpecificException as e:
    # Specific Error Handling
    return error_template_response()
except Exception as e:
    # General Error Handling
    logger.error(f"Unexpected error: {e}")
    return general_error_response()
```

## Performance-Considerations

### Database Performance
- **Lazy Loading**: PonyORM nutzt standardmäßig Lazy Loading
- **Query Optimization**: Gezieltes Laden benötigter Daten
- **Connection Pooling**: Für Production-Environment

### Frontend Performance
- **Static Files**: Effiziente Delivery über FastAPI StaticFiles
- **Template Caching**: Jinja2 Template-Caching aktivieren
- **Minimal JavaScript**: Fokus auf Server-side Rendering

## Deployment-Guidelines

### Development Environment
```bash
# Standard Development Setup
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Production Environment
- **Database**: PostgreSQL statt SQLite
- **Reverse Proxy**: Nginx oder Apache vor FastAPI
- **Process Management**: systemd oder Windows Service
- **Monitoring**: Health Checks und Log Monitoring

## Git-Workflow

### Commit Conventions
```
feat: neue Funktionalität
fix: Bug-Fix
docs: Dokumentation
refactor: Code-Refactoring
test: Test-Ergänzungen
config: Konfiguration-Änderungen
```

### Branch Strategy
- **main**: Produktionsbereiter Code
- **feature/**: Neue Features
- **bugfix/**: Bug-Fixes
- **hotfix/**: Kritische Production-Fixes

## Troubleshooting

### Häufige Probleme
1. **Scheduler Jobs not loading**: Datenbank-Verbindung prüfen
2. **Template not found**: Template-Pfad in Jinja2 konfigurieren
3. **Database locked**: SQLite-Verbindungen nicht ordentlich geschlossen
4. **E-Mail not sending**: SMTP-Konfiguration in .env prüfen

### Debug-Strategien
- **FastAPI Debug Mode**: Detaillierte Error-Pages
- **Database Introspection**: SQLite-Browser für Schema-Prüfung
- **Log Analysis**: Print-Statements für Request-Flow
- **API Testing**: FastAPI /docs für Endpoint-Testing

## Maintenance

### Regular Tasks
- **Database Backup**: Regelmäßige SQLite-Backups
- **Log Rotation**: Log-Files bereinigen
- **Dependency Updates**: requirements.txt aktualisieren
- **Security Updates**: Regelmäßige Security-Patches

### Code Review Checklist
- [ ] Authentication/Authorization korrekt implementiert
- [ ] Database Sessions ordentlich verwaltet
- [ ] Error Handling implementiert
- [ ] Template-Response korrekt strukturiert
- [ ] No hardcoded secrets in Code
- [ ] Tests für neue Funktionalität
