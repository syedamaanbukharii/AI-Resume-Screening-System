"""Job CRUD and authorization tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _create_job(client: AsyncClient) -> dict:
    """Create a job and return the response JSON."""
    resp = await client.post(
        "/api/v1/jobs",
        json={
            "title": "Senior ML Engineer",
            "description_raw": "Build and ship ML systems.",
            "required_skills": ["python", "pytorch"],
        },
    )
    return resp


@pytest.mark.asyncio
async def test_create_and_get_job(auth_client: AsyncClient) -> None:
    """A recruiter can create and fetch a job."""
    created = await _create_job(auth_client)
    assert created.status_code == 201
    job_id = created.json()["id"]

    got = await auth_client.get(f"/api/v1/jobs/{job_id}")
    assert got.status_code == 200
    assert got.json()["title"] == "Senior ML Engineer"


@pytest.mark.asyncio
async def test_list_and_status_change(auth_client: AsyncClient) -> None:
    """Status change archives a job and default scoring weights apply."""
    created = await _create_job(auth_client)
    job_id = created.json()["id"]

    patched = await auth_client.patch(
        f"/api/v1/jobs/{job_id}/status", json={"status": "closed"}
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "closed"

    listed = await auth_client.get("/api/v1/jobs", params={"status": "closed"})
    assert listed.status_code == 200
    assert any(j["id"] == job_id for j in listed.json())


@pytest.mark.asyncio
async def test_delete_archives_job(auth_client: AsyncClient) -> None:
    """Deleting a job soft-archives it."""
    created = await _create_job(auth_client)
    job_id = created.json()["id"]
    deleted = await auth_client.delete(f"/api/v1/jobs/{job_id}")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "archived"


@pytest.mark.asyncio
async def test_jobs_require_auth(client: AsyncClient) -> None:
    """Unauthenticated access to jobs is rejected."""
    resp = await client.get("/api/v1/jobs")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_status_rejected(auth_client: AsyncClient) -> None:
    """An invalid status transition is a validation error."""
    created = await _create_job(auth_client)
    job_id = created.json()["id"]
    resp = await auth_client.patch(
        f"/api/v1/jobs/{job_id}/status", json={"status": "bogus"}
    )
    assert resp.status_code == 422
