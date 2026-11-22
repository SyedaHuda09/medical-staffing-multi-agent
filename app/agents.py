from typing import List
from .models import StaffMember, Shift, Assignment, UnfilledShift


class DemandAnalysisAgent:
    """Prioritizes urgent shifts, then date and ID for reproducibility."""

    def run(self, shifts: List[Shift]):
        ordered = sorted(shifts, key=lambda s: (-s.priority, s.date, s.id))
        return ordered, [f"Prioritized {len(ordered)} open shift(s); highest priority first."]


class EligibilityAgent:
    """Applies hard role, availability, skill, and weekly-hour constraints."""

    def eligible(self, staff: StaffMember, shift: Shift, current_hours: int):
        if staff.role != shift.role_required:
            return False, "role mismatch"
        if shift.shift_type not in staff.available_shifts:
            return False, "not available for this shift type"
        missing = sorted(set(shift.required_skills) - set(staff.skills))
        if missing:
            return False, "missing required skill(s): " + ", ".join(missing)
        if current_hours + shift.hours > staff.max_weekly_hours:
            return False, "weekly hour limit would be exceeded"
        return True, "all hard constraints satisfied"


class AllocationAgent:
    """Selects the eligible person with the lowest current-hours utilization."""

    def run(self, staff: List[StaffMember], shifts: List[Shift]):
        assignments, unfilled, audit = [], [], []
        current_hours = {person.id: person.assigned_weekly_hours for person in staff}
        eligibility = EligibilityAgent()

        for shift in shifts:
            candidates, rejected = [], []
            for person in staff:
                ok, reason = eligibility.eligible(person, shift, current_hours[person.id])
                if ok:
                    ratio = current_hours[person.id] / person.max_weekly_hours
                    candidates.append((ratio, person.id, person))
                else:
                    rejected.append(f"{person.id}: {reason}")

            candidates.sort(key=lambda item: (item[0], item[1]))
            if not candidates:
                reason = "; ".join(rejected) if rejected else "No staff records supplied."
                unfilled.append(UnfilledShift(shift_id=shift.id, reason=reason))
                audit.append(f"Shift {shift.id} left unfilled: {reason}")
                continue

            _, _, chosen = candidates[0]
            before = current_hours[chosen.id]
            current_hours[chosen.id] += shift.hours
            explanation = (
                f"Role '{shift.role_required}', shift '{shift.shift_type}', and required "
                f"skills [{', '.join(shift.required_skills)}] matched. Hours: {before} -> "
                f"{current_hours[chosen.id]} of {chosen.max_weekly_hours}. "
                "Selected by lowest utilization."
            )
            assignments.append(Assignment(
                shift_id=shift.id, staff_id=chosen.id,
                staff_name=chosen.name, explanation=explanation
            ))
            audit.append(f"Shift {shift.id} assigned to {chosen.id}. {explanation}")

        return assignments, unfilled, audit


class ComplianceAuditAgent:
    """Independently re-checks every assignment before returning a report."""

    def run(self, staff, shifts, assignments):
        staff_by_id = {person.id: person for person in staff}
        shift_by_id = {shift.id: shift for shift in shifts}
        totals = {person.id: person.assigned_weekly_hours for person in staff}

        for assignment in assignments:
            person = staff_by_id[assignment.staff_id]
            shift = shift_by_id[assignment.shift_id]
            totals[person.id] += shift.hours
            assert person.role == shift.role_required
            assert shift.shift_type in person.available_shifts
            assert set(shift.required_skills).issubset(set(person.skills))
            assert totals[person.id] <= person.max_weekly_hours

        notes = [
            "Audit passed: role, availability, skills, and weekly-hour constraints checked.",
            "Human review is required before any real-world roster is published."
        ]
        return notes, totals


class StaffingOrchestrator:
    """Coordinates specialist agents into one explainable allocation pipeline."""

    def __init__(self):
        self.demand_agent = DemandAnalysisAgent()
        self.allocation_agent = AllocationAgent()
        self.audit_agent = ComplianceAuditAgent()

    def run(self, staff: List[StaffMember], shifts: List[Shift]):
        ordered_shifts, demand_notes = self.demand_agent.run(shifts)
        assignments, unfilled, allocation_notes = self.allocation_agent.run(staff, ordered_shifts)
        audit_notes, totals = self.audit_agent.run(staff, ordered_shifts, assignments)
        return {
            "assignments": assignments,
            "unfilled_shifts": unfilled,
            "audit": demand_notes + allocation_notes + audit_notes,
            "summary": {
                "total_shifts": len(shifts),
                "assigned": len(assignments),
                "unfilled": len(unfilled),
                "final_weekly_hours_by_staff": totals
            }
        }
