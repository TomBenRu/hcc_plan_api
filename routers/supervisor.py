from uuid import UUID

from fastapi import APIRouter, Request, HTTPException, status, Depends

from databases import schemas
from databases.enums import AuthorizationTypes
from databases.services import create_account, delete_a_account
from oauth2_authentication import verify_access_token, oauth2_scheme

router = APIRouter(prefix='/su', tags=['Superuser'])


@router.post('/account')
async def new_account(person: schemas.PersonCreate, project: schemas.ProjectCreate,
                      access_token: str = Depends(oauth2_scheme)):
    try:
        verify_access_token(access_token, AuthorizationTypes.supervisor)
    except Exception as e:
        raise e
    try:
        new_admin = create_account(person=person, project=project)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f'Error: {e}')

    return new_admin
