from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.post("/generate")
def generate_optimization(request: dict):
    return {
        "scenarioId": "opt-2025-1206",
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "actions": [
            {
                "deviceId": "hvac-002",
                "command": "SET_TEMPERATURE",
                "params": {"value": 19},
                "executeAt": "2025-12-06T18:00:00Z"
            }
        ],
        "recommendations": [
            "Reduce HVAC load between 17:00 and 19:00 due to tariff spike"
        ]
    }

@router.post("/send-to-iot")
def send_to_iot(request: dict):
    return {
        "status": "sent",
        "scenarioId": request["scenarioId"]
    }

@router.get("/scenario/{scenarioId}")
def scenario_details(scenarioId: str):
    return {
        "scenarioId": scenarioId,
        "buildingId": "building-A",
        "scenarioType": "peak_shaving",
        "createdAt": "2025-12-06T09:15:00Z",
        "generatedBy": "ForecastEngine-v3.2",
        "status": "ready"
    }
