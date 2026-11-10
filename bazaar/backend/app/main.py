from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import engine, init_db
from .data.market_feed import pypsx_feed
from .api import market_data, trading, predict, config as config_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    pypsx_feed.close()
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_data.router)
app.include_router(trading.router)
app.include_router(predict.router)
app.include_router(config_router.router)

@app.get("/")
async def root():
    return {"message": "Bazaar PSX Terminal API", "version": settings.APP_VERSION}
