from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# --- Універсальні структури ---

class TimeSeriesPoint(BaseModel):
    """A point of data for consumption history, forecast, or tariffs."""
    timestamp: datetime
    value: float

class HistoricalData(BaseModel):
    """Collected historical data for the model (used internally by ForecastingService)."""
    building_id: str
    telemetry: List[TimeSeriesPoint]
    weather_context: Optional[Dict[str, Any]] = None

# --- Вхідні Request DTOs (Важливо для FastAPI) ---

class ForecastRequest(BaseModel):
    """Request body for POST /forecast/generate and POST /forecast/peak-load."""
    buildingId: str
    forecastHorizonHours: int = Field(..., description="Forecast horizon in hours")


class OptimizationRequest(BaseModel):
    """Request body for POST /optimization/generate."""
    buildingId: str
    targetPeriodHours: int
    objectives: List[str] = Field(default=["cost_reduction", "peak_shaving"])


class ScenarioSendRequest(BaseModel):
    """Request body for POST /optimization/send-to-iot."""
    scenarioId: str
    # Actions definition is simplified, but should match ControlAction structure
    actions: List[Dict[str, Any]]


# --- Прогнозування (Forecast DTOs) ---

class PeakPeriod(BaseModel):
    """A detected period of peak load (used in POST /forecast/peak-load response)."""
    start: datetime
    end: datetime
    estimatedLoad: float  # Renamed to match API spec
    reason: str = "High Demand & High Tariff"


class DevicePredictionPoint(BaseModel):
    """A single prediction point with confidence (used in GET /forecast/prediction/{deviceId})."""
    timestamp: datetime
    predictedValue: float
    confidence: float


class DevicePredictionResponse(BaseModel):
    """Response structure for GET /forecast/prediction/{deviceId}."""
    deviceId: str
    metric: str
    interval: str
    timeRange: Dict[str, datetime]
    predictionPoints: List[DevicePredictionPoint]
    modelInfo: Dict[str, Any]

class DeviceImpact(BaseModel):
    """Expected energy/cost impact for a single action."""
    energySaving_kWh: float # Renamed to match API spec
    costSaving_eur: float

class DeviceRecommendationPoint(BaseModel):
    """A detailed recommendation point for a specific device (used in GET /forecast/optimization/{deviceId})."""
    timestamp: datetime
    action: str
    parameters: Dict[str, Any]
    reason: str
    expectedImpact: DeviceImpact # Pydantic requires this dependency

class ScenarioDetailsResponse(BaseModel):
    """Response structure for GET /optimization/scenario/{scenarioId}."""
    scenarioId: str
    buildingId: str
    scenarioType: str
    createdAt: datetime
    timeRange: Dict[str, datetime]
    recommendedActions: List[Dict[str, Any]]
    aggregateImpact: Dict[str, Any]
    status: str


class ForecastData(BaseModel):
    forecastId: str
    buildingId: str
    generatedAt: datetime
    horizonHours: int
    predictions: List[TimeSeriesPoint]
    summary: Dict[str, Any]


class AdminRecommendation(BaseModel):
    actionType: str
    justification: str
    potentialSavings: float


class ControlAction(BaseModel):
    deviceId: str
    command: str
    executeAt: datetime
    params: Dict[str, Any] = Field(default_factory=dict)


class OptimizationScenario(BaseModel):
    scenarioId: str
    buildingId: str
    generatedAt: datetime
    appliesFrom: datetime
    totalEnergySaving_kWh: float
    estimatedCostSaving_usd: float
    actions: List[ControlAction]