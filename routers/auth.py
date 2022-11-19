from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from databases.enums import AuthorizationTypes
from databases.pydantic_models import Token
from oauth2_authentication import create_access_token, verify_supervisor_username, verify_supervisor_password

router = APIRouter(tags=['Authentication'])


@router.get('/su/login', response_model=Token)
def supervisor_login(email: str, password: str):
    if not verify_supervisor_username(email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')
    if not verify_supervisor_password(password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'supervisor': 'supervisor',
                                             'authorization': AuthorizationTypes.supervisor.value})

    return {'access_token': access_token, 'token_type': 'bearer'}

