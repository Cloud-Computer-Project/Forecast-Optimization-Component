from fastapi import FastAPI
from app.routers import forecast, optimization

app = FastAPI(
    title="Forecast & Optimization Service",
    version="1.0.0"
)

app.include_router(forecast.router, prefix="/forecast", tags=["Forecast"])
app.include_router(optimization.router, prefix="/optimization", tags=["Optimization"])
