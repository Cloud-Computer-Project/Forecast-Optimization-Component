from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.core.interfaces import IDataClient
from app.core.models.dto import HistoricalData, TimeSeriesPoint, OptimizationScenario


class ExternalDataClient(IDataClient):
    """
    IDataClient realization
    Imitates calls to Data Storage API, External Tariffs API та IoT & Control Service.
    """

    def __init__(self):
        print("ExternalDataClient initialized. Ready to fetch data.")

    def fetch_historical_data(self, building_id: str, duration_days: int) -> HistoricalData:
        """
        Imitates /storage/consumption/history call
        Generates consumption data for a given period of time
        """
        print(f"Fetching {duration_days} days of historical data for {building_id}...")

        end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(days=duration_days)

        telemetry: List[TimeSeriesPoint] = []

        # Generates 24 points per day
        current_time = start_time
        while current_time < end_time:
            # simulation of power fluctuations
            hour_of_day = current_time.hour
            base_power = 80 + (hour_of_day * 4) + (20 * (hour_of_day < 8 or hour_of_day > 20))
            telemetry.append(TimeSeriesPoint(timestamp=current_time, value=base_power))
            current_time += timedelta(hours=1)

        # Mock weather data
        weather_context = {"temperature": 25.0, "is_sunny": True, "humidity": 60}

        return HistoricalData(
            building_id=building_id,
            telemetry=telemetry,
            weather_context=weather_context
        )

    def fetch_current_tariffs(self, region: str) -> List[TimeSeriesPoint]:
        """
        Imitates External API call for getting tariffs data (/external/tariffs/current).
        Creating a fictitious tariff that is high during peak hours.
        """
        print(f"Fetching current tariffs for {region}...")
        tariffs: List[TimeSeriesPoint] = []

        start_time = datetime.now().replace(minute=0, second=0, microsecond=0)

        for i in range(24):  # tariff forecasting for 24 hours
            time = start_time + timedelta(hours=i)
            # High tariff from 17:00 to 20:00
            price = 0.15
            if 17 <= time.hour < 20:
                price = 0.35  # Peak price

            tariffs.append(TimeSeriesPoint(timestamp=time, value=price))

        return tariffs

    def send_control_scenario(self, scenario: OptimizationScenario) -> bool:
        """
        Imitates POST /iot/optimization/apply.
        Sending final scenario to IoT & Control Service.
        """
        print("-" * 50)
        print(f"SENT TO IOT SERVICE: Scenario {scenario.scenarioId}")
        print(f"Actions count: {len(scenario.actions)}")
        print(f"Estimated Cost Saving: ${scenario.estimatedCostSaving_usd:.2f}")
        print("-" * 50)
        return True