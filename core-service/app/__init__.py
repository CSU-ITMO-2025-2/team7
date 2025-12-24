from fastapi import FastAPI

from .api import router
from .clients import close_kafka_producer
from .database import Base, engine

app = FastAPI(title="Distributed Core Service")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def on_shutdown():
    close_kafka_producer()


app.include_router(router)
