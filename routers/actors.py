from fastapi import HTTPException, status, APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from starlette.datastructures import URL
from starlette.responses import RedirectResponse

from databases import services
from databases.enums import AuthorizationTypes
from oauth2_authentication import get_current_user_cookie, verify_actor_username
from utilities import send_mail
from utilities.send_mail import send_remainder_confirmation, send_confirmed_avail_days

templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix='/actors', tags=['Actors'])


@router.get('/plan-periods')
def actor_plan_periods(request: Request):
    try:
        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    except Exception as e:
        redirect_url = URL(request.url_for('home')).include_query_params(confirmed_password=False)
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        # return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Fehler: {e}')
    user_id = token_data.id

    user = services.Person.get_user_by_id(user_id)
    name_project = user.project.name
    plan_per_et_filled_in = services.PlanPeriod.get_open_plan_periods(user_id)

    response = templates.TemplateResponse('index_actor.html',
                                          context={'request': request, 'name_project': name_project,
                                                   'f_name': user.f_name, 'l_name': user.l_name,
                                                   'plan_periods': plan_per_et_filled_in, 'actor_id': user.id,
                                                   'success': None})

    return response


@router.post('/plan-periods-handler')
async def actor_plan_periods_handler(request: Request):
    try:
        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    except Exception as e:
        redirect_url = URL(request.url_for('home')).include_query_params(confirmed_password=False)
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        #return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Fehler: {e}')
    user_id = token_data.id

    formdata = await request.form()

    plan_periods = services.AvailDay.available_days_to_db(dict(formdata), user_id)

    user = services.Person.get_user_by_id(user_id)
    name_project = user.project.name
    plan_per_et_filled_in = services.PlanPeriod.get_open_plan_periods(user_id)

    send_confirmed_avail_days(user.id)

    return templates.TemplateResponse('index_actor.html',
                                      context={'request': request, 'name_project': name_project,
                                               'f_name': user.f_name, 'l_name': user.l_name,
                                               'plan_periods': plan_per_et_filled_in, 'actor_id': user.id,
                                               'success': True})


@router.get('/new_passwort')
def send_new_password(request: Request, user_email: EmailStr):
    try:
        user = verify_actor_username(username=user_email)
        if not user:
            return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'User nicht gefunden.')
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'User nicht gefunden: {e}')
    user_id = user.id

    try:
        project = services.Project.get_project_from_user_id(user_id=user_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler2: {e}')
    try:
        person, new_password = services.Person.set_new_password(user_id=user_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler3: {e}')
    try:
        send_mail.send_new_password(person=person, project=project.name, new_psw=new_password)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler4: {e}')

    return templates.TemplateResponse('index_new_passwort.html',
                                      context={'request': request, 'name_project': project.name,
                                               'f_name': person.f_name, 'l_name': person.l_name, 'email': person.email})
