from fastapi import HTTPException, status, APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import EmailStr
from starlette.responses import RedirectResponse

from databases.enums import AuthorizationTypes
from databases.services import get_user_by_id
from oauth2_authentication import verify_actor_username, create_access_token, get_current_user_cookie
from utilities import utils

templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix='', tags=['home'])


@router.get('/')
def home(request: Request):
    try:
        token_data = get_current_user_cookie(request, 'access_token_actor', AuthorizationTypes.actor)
    except Exception as e:
        return templates.TemplateResponse('index.html', context={'request': request, 'InvalidCredentials': False})
    user_id = token_data.id

    user = get_user_by_id(user_id)
    name_project = user.project.name
    response = templates.TemplateResponse('index_home.html',
                                          context={'request': request, 'name_project': name_project,
                                                   'f_name': user.f_name, 'l_name': user.l_name})
    return response



@router.post('/home')
def home_2(request: Request, email: EmailStr = Form(...), password: str = Form(...)):
    if not (user := verify_actor_username(username=email)):
        return templates.TemplateResponse('index.html', context={'request': request, 'InvalidCredentials': True})
    if not utils.verify(password, user.password):
        return templates.TemplateResponse('index.html', context={'request': request, 'InvalidCredentials': True})
    access_token = create_access_token(data={'user_id': user.id, 'authorization': AuthorizationTypes.actor.value})

    name_project = user.project.name
    f_name = user.f_name
    l_name = user.l_name
    response = templates.TemplateResponse('index_home.html',
                                          context={'request': request, 'name_project': name_project,
                                                   'f_name': f_name, 'l_name': l_name})
    response.set_cookie(key='access_token_actor', value=access_token, httponly=True)

    return response


@router.get('/logout')
def logout(request: Request):
    try:
        token_data = get_current_user_cookie(request, 'access_token_actor', AuthorizationTypes.actor)
    except Exception as e:
        return templates.TemplateResponse('index.html', context={'request': request, 'InvalidCredentials': False,
                                                                 'logged_out': True})
    user_id = token_data.id
    response = templates.TemplateResponse('index.html',
                                          context={'request': request, 'InvalidCredentials': False,
                                                                 'logged_out': True})
    response.delete_cookie('access_token_actor')
    return response


