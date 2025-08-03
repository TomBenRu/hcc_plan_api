# Code Style & Konventionen - hcc_plan_api

## Allgemeine Code-Konventionen
- **Python Style**: Folgt PEP 8 Richtlinien
- **Encoding**: UTF-8 für alle Textdateien
- **Line Endings**: Windows-Style (CRLF) entsprechend der Entwicklungsumgebung

## Naming Conventions
- **Variablen & Funktionen**: snake_case (z.B. `user_id`, `get_current_user`)
- **Klassen**: PascalCase (z.B. `Person`, `PlanPeriod`, `APSchedulerJob`)
- **Konstanten**: UPPER_SNAKE_CASE (z.B. `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Private Methods**: Mit führendem Unterstrich (z.B. `_internal_method`)
- **Dateinamen**: snake_case.py (z.B. `oauth2_authentication.py`)

## Projektstruktur-Konventionen
- **routers/**: FastAPI Router-Module nach Rollen organisiert
- **databases/**: Datenbank-Layer mit models.py, schemas.py, services.py
- **templates/**: Jinja2-HTML-Templates mit sprechenden Namen
- **utilities/**: Helper-Module für Cross-cutting Concerns
- **static/**: Frontend-Assets (CSS, JS, Images)

## Datenbank-Modelling (PonyORM)
- **Entity Classes**: PascalCase mit beschreibenden Namen
- **Primärschlüssel**: UUID als Standard, `id = PrimaryKey(UUID, auto=True)`
- **Zeitstempel**: `created_at`, `last_modified` mit automatischen Defaults
- **Beziehungen**: Aussagekräftige Namen (z.B. `team_of_actor`, `teams_of_dispatcher`)
- **Before-Hooks**: `before_insert()`, `before_update()` für Business Logic

## FastAPI Router-Konventionen
```python
router = APIRouter(prefix='/actors', tags=['Actors'])

@router.get('/plan-periods')
def actor_plan_periods(request: Request):
    # Authentication Check
    try:
        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    except Exception as e:
        # Redirect or Error Handling
        
    # Business Logic
    # Template Response
```

## Authentication Pattern
- **Cookie-based**: `get_current_user_cookie()` für Web-Routes
- **Role Verification**: `AuthorizationTypes.actor/admin/supervisor/dispatcher`
- **Error Handling**: Try-catch mit Redirect oder Template-Response

## Template-Response Pattern
```python
return templates.TemplateResponse('template_name.html',
                                 context={'request': request, 
                                         'data': data,
                                         'user': user})
```

## Service Layer Pattern
- **Static Methods**: Für stateless Service-Operationen
- **DB Session Management**: PonyORM `@db_session` decorator
- **Error Handling**: Custom Exceptions für Business Logic

## Configuration Management
```python
class Settings(BaseSettings):
    """Reads variables from .env file"""
    variable_name: str
    
    class Config:
        env_file = '.env'
```

## Scheduler Job Pattern
```python
# Job Definition mit APScheduler
scheduler.add_job(
    func=function_name,
    trigger='cron',
    **job_parameters
)
```

## Database Model Conventions
- **Composite Keys**: Für eindeutige Kombinationen (z.B. f_name + l_name + project)
- **Required vs Optional**: Explizite Null-Behandlung
- **Set Relationships**: Für Many-to-Many Beziehungen
- **Property Methods**: Für berechnete Eigenschaften

## Error Handling
- **Custom Exceptions**: Domain-spezifische Error-Klassen
- **Template Error Pages**: Benutzerfreundliche Error-Anzeige
- **Graceful Degradation**: Fallback-Verhalten bei Fehlern

## Testing Conventions
- **Test Files**: test.py, test_2.py, test_3.py für verschiedene Aspekte
- **Isolation**: Separate Test-Datenbanken
- **Mocking**: Scheduler und externe Services

## Documentation
- **Inline Comments**: Für komplexe Business Logic
- **Docstrings**: Für öffentliche Methods (deutsch)
- **Type Hints**: Vollständige Typisierung wo möglich

## File Organization
- **Single Responsibility**: Ein Konzept pro Datei
- **Logical Grouping**: Verwandte Funktionalität zusammenfassen
- **Import Organization**: Standard Library → Third Party → Local Imports
