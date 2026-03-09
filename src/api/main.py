from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import create_db_and_tables
from .backup import start_backup_scheduler
from .routers import families, members, chores


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    scheduler = start_backup_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(title="HouseFair API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(families.router)
app.include_router(members.router)
app.include_router(chores.router)


@app.get("/health")
def health():
    return {"status": "ok"}
