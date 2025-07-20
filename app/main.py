from api import api_router
from fastapi import FastAPI

app = FastAPI(title="Python technical test")

app.include_router(api_router)
