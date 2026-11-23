"""Contract parity: backend Pydantic accepts the same fixtures frontend Zod accepts.

Mirrors frontend/lib/__tests__/contracts.test.ts cases. Catches drift between
backend/app/models/schemas.py and contracts/*.schema.json by validating the
shipped JSON schemas are well-formed and cover the same op set.
"""
import json
from pathlib import Path

import pytest

from backend.app.models.schemas import EditPlan

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> dict:
    return json.loads((ROOT / "contracts" / name).read_text())


def test_edit_plan_schema_wellformed():
    schema = _load("edit-plan.schema.json")
    assert schema["title"] == "EditPlan"
    assert set(schema["properties"]["ops"]["items"]["properties"]["op"]["enum"]) == {
        "cut", "keep", "speed", "caption"}


def test_job_schema_wellformed():
    schema = _load("job.schema.json")
    assert schema["title"] == "Job"
    assert "jobId" in schema["properties"]


def test_backend_accepts_frontend_fixture():
    plan = EditPlan.model_validate({
        "version": "v1",
        "ops": [{"op": "cut", "start": 0, "end": 2}],
        "response": "results",
    })
    assert len(plan.ops) == 1


def test_backend_rejects_unknown_op():
    with pytest.raises(Exception):
        EditPlan.model_validate({
            "version": "v1",
            "ops": [{"op": "dissolve", "start": 0, "end": 1}],
        })


def test_backend_rejects_bad_speed():
    with pytest.raises(Exception):
        EditPlan.model_validate({
            "version": "v1",
            "ops": [{"op": "speed", "start": 0, "end": 1, "factor": 9}],
        })
