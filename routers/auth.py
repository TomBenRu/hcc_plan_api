from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from databases import schemas
from databases.enums import AuthorizationTypes
from oauth2_authentication import authenticate_user, create_access_token, get_authorization_types

router = APIRouter(tags=['Authentication'])


@router.post('/token')
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate_user(form_data.username, form_data.password)
    except Exception as e:
        raise e
    if user == 'supervisor':
        access_token = create_access_token(data={'user_id': 'supervisor',
                                                 'roles': [AuthorizationTypes.supervisor.value]})
    else:
        auth_types = get_authorization_types(user)
        access_token = create_access_token(data={'user_id': str(user.id),
                                                 'roles': [a_t.value for a_t in auth_types]})
    return schemas.Token(access_token=access_token, token_type='bearer')


@router.post('/user-login-from-clown-control', status_code=status.HTTP_200_OK)
async def user_login_from_clown_control(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate_user(form_data.username, form_data.password)
    except Exception as e:
        raise e
    auth_types = get_authorization_types(user)
    if AuthorizationTypes.actor not in auth_types:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='You are not authorized')
    return {'f_name': user.f_name, 'l_name': user.l_name, 'artost_name': user.artist_name, 'team_of_actor': user.team_of_actor.name,
            'institution_actors': user.project.name}
