from fastapi import HTTPException, status, APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import EmailStr
from starlette.datastructures import URL
from starlette.responses import RedirectResponse

from databases import services
from databases.enums import AuthorizationTypes
from oauth2_authentication import verify_actor_username, get_current_user_cookie, \
    authenticate_user, create_access_token, get_authorization_types
from utilities import utils

templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix='', tags=['home'])


@router.get('/')
def home(request: Request):
    try:
        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    except Exception as e:
        return templates.TemplateResponse('index.html', context={'request': request, 'InvalidCredentials': False})
    user_id = token_data.id

    user = services.Person.get_user_by_id(user_id)
    if user is None:
        return templates.TemplateResponse('index.html', context={'request': request, 'InvalidCredentials': False})
    name_project = user.project.name
    response = templates.TemplateResponse('index_home.html',
                                          context={'request': request, 'name_project': name_project,
                                                   'f_name': user.f_name, 'l_name': user.l_name})
    return response


@router.post('/home')
def home_2(request: Request, email: EmailStr = Form(...), password: str = Form(...)):
    try:
        user = authenticate_user(email, password)
    except Exception as e:
        return templates.TemplateResponse('index.html', context={'request': request, 'InvalidCredentials': True})
    if not user.team_of_actor:
        return templates.TemplateResponse('index.html', context={'request': request, 'InvalidCredentials': True})
    auth_types = get_authorization_types(user)
    access_token = create_access_token(data={'user_id': str(user.id),
                                             'roles': [a_t.value for a_t in auth_types]})

    name_project = user.project.name
    f_name = user.f_name
    l_name = user.l_name
    response = templates.TemplateResponse('index_home.html',
                                          context={'request': request, 'name_project': name_project,
                                                   'f_name': f_name, 'l_name': l_name})
    response.set_cookie(key='hcc_plan_auth', value=access_token, httponly=True)

    return response


@router.get('/logout')
def logout(request: Request):
    try:
        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    except Exception as e:
        return templates.TemplateResponse('index.html',
                                          context={'request': request, 'InvalidCredentials': False, 'logged_out': True})
    user_id = token_data.id
    response = templates.TemplateResponse('index.html',
                                          context={'request': request, 'InvalidCredentials': False, 'logged_out': True})
    response.delete_cookie('hcc_plan_auth')
    return response


@router.get('/account')
def account_settings(request: Request, confirmed_password: bool = True):
    try:
        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    except Exception as e:
        return templates.TemplateResponse('index.html', context={'request': request,
                                                                 'InvalidCredentials': False, 'logged_out': False})
    user_id = token_data.id
    user = services.Person.get_user_by_id(user_id)
    name_project = user.project.name

    return templates.TemplateResponse('account_settings_actor.html',
                                      context={'request': request, 'name_project': name_project,
                                               'f_name': user.f_name, 'l_name': user.l_name, 'email': user.email,
                                               'confirmed_password': confirmed_password})


@router.post('/account')
def write_new_account_settings(request: Request, email: EmailStr = Form(...), password: str = Form(...),
                               confirmed_password: str = Form(...)):
    try:
        token_data = get_current_user_cookie(request, 'hcc_plan_auth', AuthorizationTypes.actor)
    except Exception as e:
        return RedirectResponse(request.url_for('home'), status_code=status.HTTP_303_SEE_OTHER)
    if password != confirmed_password:
        redirect_url = URL(request.url_for('account_settings')).include_query_params(confirmed_password=False)
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    user_id = token_data.id

    try:
        person = services.Person.set_new_actor_account_settings(person_id=user_id, new_email=email, new_password=password)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')

    response = templates.TemplateResponse('index.html',
                                          context={'request': request, 'InvalidCredentials': False, 'logged_out': False,
                                                   'account_changed': True})
    response.delete_cookie('hcc_plan_auth')
    return response
