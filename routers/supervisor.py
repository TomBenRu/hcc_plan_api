from uuid import UUID

from fastapi import APIRouter, Request, HTTPException, status, Depends

from databases import schemas, services
from databases.enums import AuthorizationTypes
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
        new_admin = services.Project.create_account(person=person, project=project)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f'Error: {e}')

    return new_admin
