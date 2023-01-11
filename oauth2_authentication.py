from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import JWTError, jwt

from databases.enums import AuthorizationTypes
import databases.pydantic_models as pm
from databases.services import find_user_by_email, get_list_of_authorizations
from settings import settings
from utilities import utils

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
SUPERVISOR_USERNAME = settings.supervisor_username
SUPERVISOR_PASSWORD = settings.supervisor_password
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                      detail='Could not validate credentials.',
                                      headers={'WWW-Authenticate': 'Bearer'})


def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({'exp': expire})
    encoded_jwt = jwt.encode(claims=data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, authorization: AuthorizationTypes) -> pm.TokenData:
    try:
        payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=ALGORITHM)
        if not (u_id := payload.get('user_id')):
            raise credentials_exception
        if authorization.value not in payload['authorization']:
            raise credentials_exception
        token_data = pm.TokenData(id=u_id, authorizations=payload['authorization'])
    except JWTError:
        raise credentials_exception
    return token_data


def get_current_user_cookie(request: Request, token_key: str, authorization: AuthorizationTypes):
    token: str | None = request.cookies.get(token_key)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='you have to log in first')

    return verify_access_token(token, authorization)


def get_authorization_types(user: pm.PersonShow) -> list[AuthorizationTypes]:
    auth_types = get_list_of_authorizations(user)
    return auth_types


def authenticate_user(username: str, passwort: str) -> pm.PersonShow | str:
    if username == SUPERVISOR_USERNAME:
        if utils.verify(passwort, SUPERVISOR_PASSWORD):
            return 'supervisor'
    if not (user := find_user_by_email(email=username)):
        raise credentials_exception
    if not utils.verify(passwort, user.password):
        raise credentials_exception
    return user


def verify_actor_username(username: str) -> pm.PersonShow | None:
    if user := find_user_by_email(username):
        if user.team_of_actor:
            return user
    return None
