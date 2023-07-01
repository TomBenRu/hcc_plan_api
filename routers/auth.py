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
