from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.core.models.dto import HistoricalData, ForecastData, TimeSeriesPoint, OptimizationScenario


class IMLModel(ABC):

    @abstractmethod
    def load_model(self, path: str) -> bool:
        pass

    @abstractmethod
    def predict(self, data: HistoricalData, horizon_hours: int) -> ForecastData:
        """
        Generates prediction. Returns full DTO ForecastData
        """
        pass

    @abstractmethod
    def train_model(self, data: HistoricalData) -> None:
        pass


class IDataClient(ABC):

    @abstractmethod
    def fetch_historical_data(self, building_id: str, duration_days: int) -> HistoricalData:
        pass

    @abstractmethod
    def fetch_current_tariffs(self, region: str) -> List[TimeSeriesPoint]:
        pass

    @abstractmethod
    def send_control_scenario(self, scenario: OptimizationScenario) -> bool:
        pass