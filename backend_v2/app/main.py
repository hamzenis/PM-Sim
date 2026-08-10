from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.classes import router as class_router
from app.api.results import router as result_router
from app.api.scenarios import router as scenario_router
from app.api.simulations import router as simulation_router
from app.db.session import get_session

app = FastAPI(title="PM-Sim API", version="0.1.0")
app.include_router(auth_router, prefix="/api")
app.include_router(class_router, prefix="/api")
app.include_router(scenario_router, prefix="/api")
app.include_router(result_router, prefix="/api")
app.include_router(simulation_router, prefix="/api")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["system"])
def readiness(session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from error
    return {"status": "ready"}
