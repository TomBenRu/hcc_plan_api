from fastapi import APIRouter, Request, HTTPException, status, Depends

import databases.pydantic_models as pm
from databases.services import create_account
from oauth2_authentication import verify_su_access_token

router = APIRouter(prefix='/su', tags=['Superuser'])


@router.post('/account')
async def new_account(person: pm.PersonCreate, project: pm.ProjectCreate, access_token: pm.Token):
    print('bin drin')
    try:
        verify_su_access_token(access_token)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e)
    try:
        print('hallo')
        new_admin = create_account(person=person, project=project)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f'Error: {e}')

    return new_admin
