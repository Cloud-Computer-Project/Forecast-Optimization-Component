from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Internal DTOs and Services (will be injected by the main app)
from app.core.models.dto import (
    ForecastRequest,
    OptimizationRequest,
    AdminRecommendation,
    OptimizationScenario,
    ControlAction,
    DevicePredictionResponse
)
from app.core.services.forecasting_service import ForecastingService
from app.core.services.optimization_service import OptimizationService


# --- DEPENDENCY STUBS (FastAPI DI mechanism) ---
# Ці функції будуть замінені реальними екземплярами сервісів у main.py
def get_forecasting_service() -> ForecastingService:
    # This will be replaced by the actual instance in main.py
    return None


def get_optimization_service() -> OptimizationService:
    # This will be replaced by the actual instance in main.py
    return None


# --- API Router Initialization ---
router = APIRouter(prefix="/api/v1", tags=["Forecast & Optimization"])


# --- 1.1 Forecast Generation (POST /forecast/generate) ---
@router.post("/forecast/generate", summary="Generates an energy demand forecast")
def post_forecast_generate(
        request: ForecastRequest,
        fs: ForecastingService = Depends(get_forecasting_service)
) -> Dict[str, Any]:
    forecast_data = fs.generate_demand_forecast(
        building_id=request.buildingId,
        horizon_hours=request.forecastHorizonHours
    )

    # Map internal ForecastData DTO to API Response structure
    response_data = {
        "forecastId": forecast_data.forecastId,
        "generatedAt": forecast_data.generatedAt.isoformat() + "Z",
        "horizonHours": forecast_data.horizonHours,
        "data": [
            {"timestamp": p.timestamp.isoformat() + "Z", "predictedLoad": p.value}
            for p in forecast_data.predictions
        ]
    }
    return response_data


# --- 1.2 Peak Load Forecasting (POST /forecast/peak-load) ---
@router.post("/forecast/peak-load", summary="Predicts periods of abnormally high energy consumption")
def post_forecast_peak_load(
        request: ForecastRequest,
        fs: ForecastingService = Depends(get_forecasting_service)
) -> Dict[str, Any]:
    peak_result = fs.generate_peak_load_forecast(
        building_id=request.buildingId,
        horizon_hours=request.forecastHorizonHours
    )
    # The service returns a dict that almost matches the API spec
    return peak_result


# --- 1.3 Optimization Scenario Generation (POST /optimization/generate) ---
"""
@router.post("/optimization/generate", summary="Creates an optimal control schedule")
def post_optimization_generate(
        request: OptimizationRequest,
        os: OptimizationService = Depends(get_optimization_service)
) -> Dict[str, Any]:
    result = os.generate_optimal_scenario(
        building_id=request.buildingId,
        target_period_hours=request.targetPeriodHours
    )

    if result["status"] == "SCENARIO_APPLIED":
        scenario: OptimizationScenario = result["scenario"]
        # Simplified response to match API spec
        return {
            "scenarioId": scenario.scenarioId,
            "generatedAt": scenario.generatedAt.isoformat() + "Z",
            "actions": [a.__dict__ for a in scenario.actions],
            "recommendations": ["Optimization completed successfully."]
        }
    else:
        # If no actions were required, return admin recommendation
        rec: AdminRecommendation = result["recommendation"]
        raise HTTPException(
            status_code=200,
            detail={"message": "No actions required", "recommendation": rec.justification}
        )
"""
@router.post(
    "/optimization/generate",
    response_model=OptimizationScenario,
    summary="Creates an optimal control schedule",
    status_code=200
)
def post_optimization_generate(
        request: OptimizationRequest,
        os: OptimizationService = Depends(get_optimization_service)
):
    scenario = os.generate_optimal_scenario(
        building_id=request.buildingId,
        target_period_hours=request.targetPeriodHours
    )
    if not scenario:
        raise HTTPException(status_code=404, detail="No optimal scenario generated for this period.")
    return scenario

# --- 1.4 Administrator Recommendations (GET /optimization/recommendations/{buildingId}) ---
@router.get("/optimization/recommendations/{buildingId}", summary="Provides general energy-saving recommendations")
def get_admin_recommendations(
        buildingId: str,
        os: OptimizationService = Depends(get_optimization_service)
) -> Dict[str, Any]:
    rec = os.generate_admin_recommendation(buildingId)
    return {
        "buildingId": buildingId,
        "generatedAt": datetime.now().isoformat() + "Z",
        "recommendations": [rec.justification, "Review equipment maintenance schedule."]
    }


# --- 1.5 Scenario Execution (GET /forecast/optimization/{deviceId}) ---
@router.get("/forecast/optimization/{deviceId}", summary="Retrieves optimization recommendations for a specific device")
def get_device_optimization(
        deviceId: str,
        scenarioType: str = Query(None),  # Optional Query Parameter
        os: OptimizationService = Depends(get_optimization_service)
) -> Dict[str, Any]:
    # Mocking implementation uses only deviceId and scenarioType
    return os.get_device_optimization_recommendations(deviceId, scenarioType)


# --- 1.6 Prediction (GET /forecast/prediction/{deviceId}) ---
@router.get("/forecast/prediction/{deviceId}", summary="Retrieves predicted consumption for a device")
def get_device_prediction(
        deviceId: str,
        interval: str = Query("1h"),
        fs: ForecastingService = Depends(get_forecasting_service)
) -> DevicePredictionResponse:
    # Mock time range for demonstration
    time_range = {"from": datetime.now(), "to": datetime.now() + timedelta(hours=24)}

    return fs.get_device_prediction(deviceId, interval, time_range)


# --- 1.7 Retrieve Scenario Details (GET /optimization/scenario/{scenarioId}) ---
@router.get("/optimization/scenario/{scenarioId}", summary="Retrieves full details of an optimization scenario")
def get_scenario_details(
        scenarioId: str,
        os: OptimizationService = Depends(get_optimization_service)
) -> Dict[str, Any]:
    try:
        return os.get_scenario_details(scenarioId)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": "scenario_not_found", "message": str(e)})