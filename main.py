import uvicorn
from fastapi import FastAPI
from app.data_clients.external_data_client import ExternalDataClient
from app.ml_implementations.sample_model import SampleMLModel
from app.core.services.forecasting_service import ForecastingService
from app.core.services.optimization_service import OptimizationService
from app.api.v1.routers import router, get_forecasting_service, get_optimization_service

# --- 1. INITIALIZE CORE SERVICES ---

# 1. Instantiate dependencies (Mocks)
ml_model = SampleMLModel()
data_client = ExternalDataClient()

# 2. Instantiate core services
# These are the singletons (only one instance) that hold the business logic
FORECASTING_SERVICE = ForecastingService(ml_model=ml_model, data_client=data_client)
OPTIMIZATION_SERVICE = OptimizationService(
    forecasting_service=FORECASTING_SERVICE,
    data_client=data_client
)

# --- 2. FASTAPI APP SETUP ---

app = FastAPI(
    title="Forecast & Optimization Component API",
    version="1.0.0",
    description="Implements all core forecasting and optimization logic for EMSIB."
)

# --- 3. DEPENDENCY OVERRIDES (Injecting Singletons) ---

# Tell FastAPI how to get the actual service instances when a route calls for Depends(...)
app.dependency_overrides[get_forecasting_service] = lambda: FORECASTING_SERVICE
app.dependency_overrides[get_optimization_service] = lambda: OPTIMIZATION_SERVICE

# --- 4. INCLUDE ROUTERS ---
app.include_router(router)

if __name__ == "__main__":
    print("Starting FastAPI Server for Forecast & Optimization Component...")
    print("You can access the interactive documentation (Swagger UI) at: http://127.0.0.1:8000/docs")

    # Uvicorn starts the server
    uvicorn.run(app, host="127.0.0.1", port=8000)