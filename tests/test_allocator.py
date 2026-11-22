from fastapi.testclient import TestClient
from app.main import app
from app.agents import StaffingOrchestrator
from app.models import StaffMember, Shift

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_demo_data_allocates_all_shifts():
    demo = client.get("/demo-data")
    response = client.post("/allocate", json=demo.json())
    assert response.status_code == 200
    assert response.json()["summary"]["assigned"] == 3


def test_missing_skill_prevents_assignment():
    staff = [StaffMember(
        id="p1", name="Sam", role="nurse", skills=["bls"],
        available_shifts=["night"], max_weekly_hours=40
    )]
    shifts = [Shift(
        id="s1", date="2026-12-01", shift_type="night",
        role_required="nurse", required_skills=["icu"], hours=8
    )]
    result = StaffingOrchestrator().run(staff, shifts)
    assert result["summary"]["unfilled"] == 1


def test_weekly_hour_limit_is_enforced():
    staff = [StaffMember(
        id="p1", name="Sam", role="nurse", skills=["icu"],
        available_shifts=["day"], max_weekly_hours=40, assigned_weekly_hours=36
    )]
    shifts = [Shift(
        id="s1", date="2026-12-01", shift_type="day",
        role_required="nurse", required_skills=["icu"], hours=8
    )]
    result = StaffingOrchestrator().run(staff, shifts)
    assert result["summary"]["unfilled"] == 1
    assert result["summary"]["final_weekly_hours_by_staff"]["p1"] == 36


def test_lowest_utilization_candidate_is_selected():
    staff = [
        StaffMember(
            id="p1", name="Alex", role="nurse", skills=["icu"],
            available_shifts=["day"], max_weekly_hours=40, assigned_weekly_hours=24
        ),
        StaffMember(
            id="p2", name="Blair", role="nurse", skills=["icu"],
            available_shifts=["day"], max_weekly_hours=40, assigned_weekly_hours=8
        )
    ]
    shifts = [Shift(
        id="s1", date="2026-12-01", shift_type="day",
        role_required="nurse", required_skills=["icu"], hours=8
    )]
    result = StaffingOrchestrator().run(staff, shifts)
    assert result["assignments"][0].staff_id == "p2"
