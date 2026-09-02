from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.auth import router as auth_router
from src.api.v1.listings import router as listing_router
from src.core.config import settings


app = FastAPI(
    title = settings.PROJECT_NAME,
    openapi_url = f"{settings.API_V1_STR}/openapi.json",
    debug = settings.DEBUG,
)

# Настройка CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
# Подключение маршрутов v1
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(listing_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}