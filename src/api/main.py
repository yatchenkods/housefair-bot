from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import auth, chores, dashboard, products, shopping, stats
from src.config import Settings
from src.database.repository import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    db = Database(settings.database_path)
    await db.connect()
    await db.init_tables()
    app.state.db = db
    app.state.settings = settings
    yield
    await db.close()


app = FastAPI(title="HouseFair API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(chores.router, prefix="/chores", tags=["chores"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(shopping.router, prefix="/shopping", tags=["shopping"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])


@app.get("/health")
async def health():
    return {"status": "ok"}
