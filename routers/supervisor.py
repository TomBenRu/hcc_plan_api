from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import EmailStr

from databases.pydantic_models import Token, DispatcherCreateBase, TeamBase, PersonBase, TokenData, AdminCreateBase, \
    ProjectBase, PersonCreateBase, PersonCreateRemoteBase
from databases.services import create_new_team, create_actor__remote, create_admin
from oauth2_authentication import (verify_supervisor_username, verify_supervisor_password, create_access_token,
                                   verify_access_token, verify_su_access_token, get_current_supervisor,
                                   get_current_user_cookie)

router = APIRouter(prefix='/su', tags=['Superuser'])


@router.post('/account')
async def new_account(person: PersonCreateRemoteBase, project: ProjectBase, access_token: Token):
    try:
        verify_su_access_token(access_token)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e)
    try:
        new_admin, password = create_admin(person=person, project=project)
    except ValueError as e:
        return HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f'Error: {e}')

    return {'new_admin': new_admin, 'password': password}
