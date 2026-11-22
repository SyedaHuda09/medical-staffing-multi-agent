from fastapi import FastAPI
from .models import AllocationRequest, AllocationResponse, StaffMember, Shift
from .agents import StaffingOrchestrator

app = FastAPI(
    title="Multi-Agent Medical Staffing API",
    description="Explainable shift-allocation demo using synthetic data.",
    version="1.0.0"
)
orchestrator = StaffingOrchestrator()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/demo-data", response_model=AllocationRequest)
def demo_data():
    return AllocationRequest(
        staff=[
            StaffMember(
                id="nurse-01", name="Amina", role="nurse",
                skills=["icu", "bls"], available_shifts=["day", "night"],
                max_weekly_hours=36, assigned_weekly_hours=8
            ),
            StaffMember(
                id="nurse-02", name="Lena", role="nurse",
                skills=["bls"], available_shifts=["day"],
                max_weekly_hours=32, assigned_weekly_hours=8
            ),
            StaffMember(
                id="doctor-01", name="Jonas", role="doctor",
                skills=["emergency"], available_shifts=["day", "night"],
                max_weekly_hours=40, assigned_weekly_hours=16
            )
        ],
        shifts=[
            Shift(
                id="shift-icu-night", date="2026-12-01", shift_type="night",
                role_required="nurse", required_skills=["icu"], hours=8, priority=3
            ),
            Shift(
                id="shift-er-day", date="2026-12-01", shift_type="day",
                role_required="doctor", required_skills=["emergency"], hours=8, priority=2
            ),
            Shift(
                id="shift-icu-day", date="2026-12-02", shift_type="day",
                role_required="nurse", required_skills=["icu"], hours=8, priority=1
            )
        ]
    )


@app.post("/allocate", response_model=AllocationResponse)
def allocate(request: AllocationRequest):
    return AllocationResponse(**orchestrator.run(request.staff, request.shifts))
