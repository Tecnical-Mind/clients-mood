from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import routes_analysis, routes_auth, routes_config
from app.config import settings
from app.deps import limiter
from app.workers import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.disable_scheduler:
        scheduler.start()
    yield
    if not settings.disable_scheduler:
        scheduler.shutdown()


app = FastAPI(title="Client's Mood API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router)
app.include_router(routes_config.router)
app.include_router(routes_analysis.router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
