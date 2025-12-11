import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.core.interfaces import IMLModel, IDataClient
from app.core.models.dto import (
    ForecastData,
    PeakPeriod,
    HistoricalData,
    DevicePredictionResponse,
    TimeSeriesPoint,
    DevicePredictionPoint  # We use DevicePredictionPoint here
)


class ForecastingService:
    """
    Core service responsible for fetching data, generating energy demand forecasts,
    peak load predictions, and serving device-specific predictions.
    """

    def __init__(self, ml_model: IMLModel, data_client: IDataClient):
        """
        Inject IMLModel and IDataClient.
        """
        self.ml_model = ml_model
        self.data_client = data_client
        self.ml_model.load_model("path/to/model.pkl")
        self.latest_forecasts: Dict[str, ForecastData] = {}  # Mock to store latest results

    def _generate_forecast_internal(self, building_id: str, horizon_hours: int, historical_days: int) -> ForecastData:
        """Internal worker function to generate the base forecast."""
        historical_data: HistoricalData = self.data_client.fetch_historical_data(
            building_id=building_id,
            duration_days=historical_days
        )
        # Preprocessing simulation
        forecast: ForecastData = self.ml_model.predict(
            data=historical_data,
            horizon_hours=horizon_hours
        )
        return forecast

    def _check_peak_load_logic(self, forecast: ForecastData) -> List[PeakPeriod]:
        """Core logic to detect peak load periods."""
        peak_periods: List[PeakPeriod] = []

        # Mock Threshold: 20% above the average load
        avg_load = sum(p.value for p in forecast.predictions) / len(forecast.predictions) if forecast.predictions else 0
        peak_threshold = avg_load * 1.2

        for point in forecast.predictions:
            if point.value > peak_threshold:
                # Note: We create a PeakPeriod Pydantic model here
                peak_periods.append(
                    PeakPeriod(
                        start=point.timestamp,
                        end=point.timestamp + timedelta(hours=3),
                        estimatedLoad=point.value,  # Renamed to match API spec
                        reason="Predicted demand exceeds 20% average."
                    )
                )
                break

        return peak_periods

    # --- API ENDPOINTS REALIZATION ---

    # Realizes POST /forecast/generate
    def generate_demand_forecast(self, building_id: str, horizon_hours: int) -> ForecastData:
        """Generates and stores the energy demand forecast."""
        print(f"[F-Service] Generating {horizon_hours}-hour forecast for {building_id}...")

        # Use mock historical days for the simulation
        forecast = self._generate_forecast_internal(building_id, horizon_hours, historical_days=7)

        # Store for the latest endpoint
        self.latest_forecasts[building_id] = forecast

        # Optionally attach peak loads to summary
        peak_loads = self._check_peak_load_logic(forecast)
        # Store as dicts for compatibility with the generic Dict[str, Any] summary field
        forecast.summary['peak_periods'] = [p.model_dump() for p in peak_loads]

        return forecast

    # Realizes POST /forecast/peak-load
    def generate_peak_load_forecast(self, building_id: str, horizon_hours: int) -> Dict[str, Any]:
        """Predicts and returns periods of high load."""
        print(f"[F-Service] Generating Peak Load Forecast for {building_id}...")

        # 1. Generate or fetch the base forecast
        forecast = self.generate_demand_forecast(building_id, horizon_hours)

        # 2. Extract peak periods
        peak_periods = self._check_peak_load_logic(forecast)

        return {
            "forecastId": f"peak-{building_id}-{datetime.now().strftime('%Y%m%d')}",
            "peakPeriods": [p.model_dump() for p in peak_periods]  # Pydantic model_dump for clean output
        }

    # Realizes GET /forecast/latest?buildingId=
    def get_latest_forecast(self, building_id: str) -> Dict[str, Any]:
        """Retrieves the latest available forecast for a building."""
        print(f"[F-Service] Retrieving latest forecast for {building_id}...")

        forecast = self.latest_forecasts.get(building_id)
        if not forecast:
            raise ValueError("Forecast not found.")

            # Format to match the API Specification response structure
        prediction_points = [
            {"timestamp": p.timestamp.isoformat() + "Z", "predictedLoad_kW": p.value,
             "confidence": 0.9 + (i % 10) / 100}
            for i, p in enumerate(forecast.predictions)
        ]

        return {
            "buildingId": building_id,
            "forecastGeneratedAt": forecast.generatedAt.isoformat() + "Z",
            "timeHorizonHours": forecast.horizonHours,
            "predictionPoints": prediction_points,
            "summary": forecast.summary
        }

    # Realizes GET /forecast/prediction/{deviceId}
    def get_device_prediction(self, device_id: str, interval: str,
                              time_range: Dict[str, datetime]) -> DevicePredictionResponse:
        """Retrieves predicted consumption for a specific device."""
        print(f"[F-Service] Retrieving prediction for device {device_id}...")

        # Mock logic: Base the device prediction on the last full building forecast
        building_id = device_id.split('-')[0]  # Simple mock to derive building ID
        forecast = self.latest_forecasts.get(building_id, None)

        prediction_points = []
        if forecast:
            # Simulate device load as a percentage of the building's total load
            for i, p in enumerate(forecast.predictions):
                device_load = p.value * 0.2 + (i % 5)
                prediction_points.append(
                    DevicePredictionPoint(
                        timestamp=p.timestamp,
                        predictedValue=device_load,
                        confidence=0.85 + (i % 10) / 100
                    )
                )

        # Note: We return the Pydantic model here, which FastAPI converts to JSON
        return DevicePredictionResponse(
            deviceId=device_id,
            metric="energy_consumption",
            interval=interval,
            timeRange=time_range,
            predictionPoints=prediction_points,
            modelInfo={"modelVersion": "v3.2.1", "predictionGeneratedAt": datetime.now()}
        )