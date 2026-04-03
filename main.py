from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
from database import SessionLocal, engine
from routers import eatics as eatics_router
from routers import router_reportes
from routers import router_precios

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GKMobile — Eatics")
templates = Jinja2Templates(directory="templates")

# Registrar routers
app.include_router(eatics_router.router)
app.include_router(router_reportes.router_reportes)
app.include_router(router_precios.router_precios)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse(url="/eatics/ejecucion-marca")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)