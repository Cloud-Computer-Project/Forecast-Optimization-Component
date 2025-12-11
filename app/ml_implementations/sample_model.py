import uuid
from datetime import datetime, timedelta
from typing import List
from app.core.interfaces import IMLModel
from app.core.models.dto import ForecastData, HistoricalData, TimeSeriesPoint  # Важливо: імпортуємо всі потрібні DTOs


class SampleMLModel(IMLModel):
    """
    Mock implementation of the ML Model interface.
    Simulates loading and prediction logic.
    """

    def __init__(self):
        print("SampleMLModel initialized. Ready to predict.")

    def load_model(self, path: str) -> None:
        """MOCK: Simulates loading the trained model."""
        pass

    def train_model(self, data: HistoricalData) -> bool:
        """
        ABSTRACT IMPLEMENTATION:
        MOCK implementation of the model training process, required by IMLModel interface.
        """
        print("MOCK: Training model using provided historical data (skipping actual training).")
        return True  # Assume training was successful

    def predict(self, data: HistoricalData, horizon_hours: int) -> ForecastData:
        """
        MOCK: Generates a sample ForecastData, ensuring all required Pydantic fields are present.
        """
        print("Generating a %d-hour forecast..." % horizon_hours)

        predictions: List[TimeSeriesPoint] = []
        # Start forecast from the next hour
        start_time = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

        # MOCK logic to create points (Simulated load curve)
        for i in range(horizon_hours):
            timestamp = start_time + timedelta(hours=i)
            # Simulate a simple load cycle
            load_value = 100.0 + 50 * ((i % 24) / 24) + (i % 10)
            predictions.append(
                TimeSeriesPoint(timestamp=timestamp, value=load_value)
            )

        # --- Створення ForecastData (Критична частина) ---
        has_predictions = bool(predictions)
        # Тут ми створюємо Pydantic-модель, передаючи всі обов'язкові поля
        return ForecastData(
            forecastId=f"fc-{data.building_id}-{str(uuid.uuid4())[:4]}",
            buildingId=data.building_id,
            generatedAt=datetime.now(),
            horizonHours=horizon_hours,
            predictions=predictions,
            summary={
                "status": "Success",
                "peakLoad_kW": max((p.value for p in predictions), default=0.0),
                "avgLoad_kW": sum(p.value for p in predictions) / len(predictions) if has_predictions else 0.0
            }
        )