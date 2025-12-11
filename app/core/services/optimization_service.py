import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.core.interfaces import IDataClient
from app.core.models.dto import (
    ForecastData,
    OptimizationScenario,
    AdminRecommendation,
    ControlAction,
    TimeSeriesPoint,
    DeviceImpact,
    DeviceRecommendationPoint,
    ScenarioDetailsResponse
)
# Note: We need to import the service we depend on for type hinting
from app.core.services.forecasting_service import ForecastingService


class OptimizationService:
    """
    Core service responsible for taking forecasts, applying cost/load optimization
    algorithms, generating control scenarios, and managing scenario data.
    """

    def __init__(self, forecasting_service: ForecastingService, data_client: IDataClient):
        self.forecasting_service = forecasting_service
        self.data_client = data_client
        self.scenario_storage: Dict[str, OptimizationScenario] = {}

    # --- Internal Logic (Optimization) ---

    def _apply_optimization_algorithm(
            self,
            forecast: ForecastData,
            tariffs: List[TimeSeriesPoint]
    ) -> OptimizationScenario:
        """Internal core optimization logic (MOCK)."""
        print("[O-Service] Applying optimization algorithm...")

        peak_tariff_point = max(tariffs, key=lambda p: p.value)
        action_time = peak_tariff_point.timestamp - timedelta(hours=1)
        actions = []

        if peak_tariff_point.value >= 0.35:  # High tariff triggers action
            actions.append(
                ControlAction(
                    deviceId="HVAC-002",
                    command="SET_TEMPERATURE",
                    executeAt=action_time,
                    params={"value": 19.0}
                )
            )
            actions.append(
                ControlAction(
                    deviceId="Lighting-010",
                    command="DIM_LIGHTS",
                    executeAt=peak_tariff_point.timestamp,
                    params={"level_pct": 70}
                )
            )

        scenario_id = f"opt-{forecast.buildingId}-{datetime.now().strftime('%H%M%S')}"
        estimated_savings = len(actions) * 5.50 if actions else 0.00
        estimated_energy_saving = len(actions) * 20.0 if actions else 0.00

        scenario = OptimizationScenario(
            scenarioId=scenario_id,
            buildingId=forecast.buildingId,
            generatedAt=datetime.now(),
            appliesFrom=action_time,
            totalEnergySaving_kWh=estimated_energy_saving,
            estimatedCostSaving_usd=estimated_savings,
            actions=actions
        )
        self.scenario_storage[scenario_id] = scenario  # Store the scenario
        return scenario

    # --- API ENDPOINTS REALIZATION ---

    # Realizes POST /optimization/generate (The Main Flow)
    def generate_optimal_scenario(self, building_id: str, target_period_hours: int) -> Dict[str, Any]:
        """Generates the full optimization scenario."""
        print(f"\n[O-Service] Starting Optimal Scenario Generation for {building_id}...")

        # 1. Request Forecast
        forecast = self.forecasting_service.generate_demand_forecast(
            building_id=building_id,
            horizon_hours=target_period_hours
        )

        # 2. Get tariffs
        tariffs = self.data_client.fetch_current_tariffs(region="UA-KYIV")

        # 3. Apply Optimization
        scenario = self._apply_optimization_algorithm(forecast, tariffs)

        if scenario.actions:
            # 4. Send to IoT (Realizes POST /optimization/send-to-iot logic)
            is_sent = self.data_client.send_control_scenario(scenario)

            if is_sent:
                return scenario

        # 5. Fallback/No actions (Realizes GET /optimization/recommendations/{buildingId} logic)
        return None
        """
        return {
            "status": "NO_ACTIONS_REQUIRED",
            "recommendation": self.generate_admin_recommendation(building_id).model_dump()
        }"""

    # Realizes GET /optimization/recommendations/{buildingId}
    def generate_admin_recommendation(self, building_id: str) -> AdminRecommendation:
        """Provides general energy-saving recommendations."""
        print(f"[O-Service] Generating general admin recommendations for {building_id}...")
        # Note: Returns Pydantic model
        return AdminRecommendation(
            actionType="Schedule Review",
            justification="Review equipment schedules for non-peak operation.",
            potentialSavings=random.uniform(50.0, 300.0)
        )

    # Realizes GET /optimization/scenario/{scenarioId}
    def get_scenario_details(self, scenario_id: str, include_forecast: bool = False) -> Dict[str, Any]:
        """Retrieves full details of a previously generated optimization scenario."""
        print(f"[O-Service] Retrieving scenario details for {scenario_id}...")

        scenario = self.scenario_storage.get(scenario_id)
        if not scenario:
            raise ValueError(f"Optimization scenario {scenario_id} does not exist.")

        # Formatting to match the API Specification
        recommended_actions = [
            {
                "deviceId": a.deviceId,
                "action": a.command,
                "timestamp": a.executeAt.isoformat() + "Z",
                "parameters": a.params,
                # Create and dump the DeviceImpact Pydantic model
                "expectedImpact": DeviceImpact(
                    energySaving_kWh=random.uniform(1.0, 5.0),
                    costSaving_eur=random.uniform(0.2, 1.2)
                ).model_dump()
            } for a in scenario.actions
        ]

        response = ScenarioDetailsResponse(
            scenarioId=scenario.scenarioId,
            buildingId=scenario.buildingId,
            scenarioType="peak_shaving",
            createdAt=scenario.generatedAt,
            timeRange={"from": scenario.appliesFrom, "to": scenario.appliesFrom + timedelta(hours=24)},
            recommended_actions=recommended_actions,
            aggregateImpact={
                "totalEnergySaving_kWh": scenario.totalEnergySaving_kWh,
                "totalCostSaving_eur": scenario.estimatedCostSaving_usd,
                "peakReduction_kW": 15.0
            },
            status="ready"
        )
        return response.model_dump()  # Use model_dump to convert to dict for FastAPI

    # Realizes GET /forecast/optimization/{deviceId}
    def get_device_optimization_recommendations(self, device_id: str, scenario_type: str) -> Dict[str, Any]:
        """Retrieves optimization recommendations for a specific device."""
        print(f"[O-Service] Retrieving device-specific recommendations for {device_id}...")

        now = datetime.now().replace(minute=0, second=0, microsecond=0)

        recommendations = [
            DeviceRecommendationPoint(
                timestamp=now + timedelta(hours=i),
                action="SET_TEMPERATURE" if "HVAC" in device_id else "DIM_LIGHTS",
                parameters={"value": 21} if "HVAC" in device_id else {"level_pct": 70},
                reason=f"Predicted high demand in next {i} hours.",
                expectedImpact=DeviceImpact(energySaving_kWh=3.2, costSaving_eur=0.85)
            ).model_dump() for i in range(1, 3)
        ]

        return {
            "deviceId": device_id,
            "scenarioType": scenario_type,
            "timeRange": {"from": now, "to": now + timedelta(hours=24)},
            "recommendations": recommendations,
            "generatedAt": datetime.now()
        }