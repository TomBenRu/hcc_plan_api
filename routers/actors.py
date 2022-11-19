from fastapi import HTTPException, status, APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr

from databases.enums import AuthorizationTypes
from databases.services import find_user_by_email, available_days_to_db, get_open_plan_periods, get_user_by_id
from oauth2_authentication import create_access_token, get_current_user_cookie, verify_actor_username
from utilities import utils

templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix='/actors', tags=['Actors'])


@router.post('/plan-periods')
def actor_plan_periods(request: Request, email: EmailStr = Form(...), password: str = Form(...)):
    if not (user := verify_actor_username(username=email)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    if not utils.verify(password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'user_id': user.id, 'authorization': AuthorizationTypes.actor.value})

    plan_per_et_filled_in = get_open_plan_periods(user.id)

    response = templates.TemplateResponse('index_actor.html',
                                          context={'request': request, 'f_name': user.f_name, 'l_name': user.l_name,
                                                   'plan_periods': plan_per_et_filled_in, 'actor_id': user.id,
                                                   'success': None})
    response.set_cookie(key='access_token_actor', value=access_token, httponly=True)

    return response


@router.post('/plan-periods-handler')
async def actor_plan_periods_handler(request: Request):
    try:
        token_data = get_current_user_cookie(request, 'access_token_actor', AuthorizationTypes.actor)
    except Exception as e:
        raise e
    user_id = token_data.id

    formdata = await request.form()

    plan_periods = available_days_to_db(dict(formdata), user_id)

    user = get_user_by_id(user_id)
    plan_per_et_filled_in = get_open_plan_periods(user_id)

    return templates.TemplateResponse('index_actor.html',
                                      context={'request': request, 'f_name': user.f_name, 'l_name': user.l_name,
                                               'plan_periods': plan_per_et_filled_in, 'actor_id': user_id,
                                               'success': True})
