import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import auth, actors, supervisor, admin, dispatcher, index

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')


app.include_router(index.router)

app.include_router(auth.router)

app.include_router(actors.router)

app.include_router(admin.router)

app.include_router(supervisor.router)

app.include_router(dispatcher.router)


if __name__ == '__main__':
    uvicorn.run(app)
    # import databases.database
