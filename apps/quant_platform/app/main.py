from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.api import stocks, strategy, market
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("QuantViz starting...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("QuantViz shutting down")


app = FastAPI(
    title="QuantViz API",
    description="Stock data visualization + quantitative strategy platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(strategy.router)
app.include_router(market.router)


@app.get("/")
async def root():
    return {"message": "QuantViz API v1.0", "docs": "/docs"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
