from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from api.routes import auth, config, ingest, search, users
from config.config import DEFAULTS
from core.db import init_db

app = FastAPI(title="arXiv agent API")


@app.on_event("startup")
def on_startup():
    init_db(DEFAULTS)


app.include_router(auth.router)
app.include_router(search.router)
app.include_router(ingest.router)
app.include_router(config.router)
app.include_router(users.router)
