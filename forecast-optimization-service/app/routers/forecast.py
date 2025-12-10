from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.post("/generate")
def generate_forecast(request: dict):
    return {
        "forecastId": "fc-2025-1220",
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "horizonHours": request["forecastHorizonHours"],
        "data": [
            {"timestamp": "2025-12-06T11:00:00Z", "predictedLoad": 120},
            {"timestamp": "2025-12-06T12:00:00Z", "predictedLoad": 118}
        ]
    }

@router.post("/peak-load")
def peak_load(request: dict):
    return {
        "forecastId": "peak-2025-1206",
        "peakPeriods": [
            {
                "start": "2025-12-07T14:00:00Z",
                "end": "2025-12-07T16:00:00Z",
                "estimatedLoad": 240
            }
        ]
    }

@router.get("/latest")
def latest(buildingId: str):
    return {
        "buildingId": buildingId,
        "forecastGeneratedAt": "2025-12-06T09:00:00Z",
        "timeHorizonHours": 24,
        "predictionPoints": [
            {"timestamp": "2025-12-06T10:00:00Z", "predictedLoad_kW": 240.5, "confidence": 0.92},
            {"timestamp": "2025-12-06T11:00:00Z", "predictedLoad_kW": 255.1, "confidence": 0.90}
        ],
        "summary": {
            "expectedPeak_kW": 290.0,
            "expectedMin_kW": 180.3,
            "expectedTotal_kWh": 5150.4
        }
    }
