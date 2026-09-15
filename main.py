from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.database import create_db_and_tables
from api.routers import upload

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="AI Wiki E-Catalog", lifespan=lifespan)

app.include_router(upload.router, prefix="/api", tags=["Upload"])

@app.get("/")
def root():
    return {"message": "Welcome to AI Wiki E-Catalog API. Backend is running!"}