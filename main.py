from fastapi import Depends, FastAPI
from routers import auth_router

app = FastAPI()

app.include_router(auth_router, tags=["auth"])


# @app.get("/test")
# async def read_users_me():
#     return {"hello": "world"}
