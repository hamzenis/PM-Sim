from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.classes import router as class_router
from app.api.scenarios import router as scenario_router

app = FastAPI(title="PM-Sim API", version="0.1.0")
app.include_router(auth_router, prefix="/api")
app.include_router(class_router, prefix="/api")
app.include_router(scenario_router, prefix="/api")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
