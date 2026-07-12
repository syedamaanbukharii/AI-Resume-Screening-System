"""API tests for resume upload and task polling."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _create_job(client: AsyncClient) -> str:
    """Create a job and return its id."""
    resp = await client.post(
        "/api/v1/jobs",
        json={"title": "ML Eng", "description_raw": "Build ML systems."},
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_upload_enqueues_parse(auth_client: AsyncClient) -> None:
    """Uploading a resume returns 202 and a task descriptor.

    The background parse itself calls the LLM/embedder, which aren't reachable
    in tests; this asserts the synchronous upload path (validate, store, enqueue).
    """
    job_id = await _create_job(auth_client)
    resp = await auth_client.post(
        f"/api/v1/jobs/{job_id}/resumes",
        files={"files": ("cv.txt", b"Jane Roe\nML Engineer\npython", "text/plain")},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert len(body) == 1
    assert body[0]["status"] == "pending"
    assert body[0]["task_id"]


@pytest.mark.asyncio
async def test_upload_rejects_bad_type(auth_client: AsyncClient) -> None:
    """An unsupported extension is rejected with 422."""
    job_id = await _create_job(auth_client)
    resp = await auth_client.post(
        f"/api/v1/jobs/{job_id}/resumes",
        files={"files": ("cv.exe", b"data", "application/octet-stream")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_task_status_lookup(auth_client: AsyncClient) -> None:
    """A created task is retrievable via the polling endpoint."""
    job_id = await _create_job(auth_client)
    upload = await auth_client.post(
        f"/api/v1/jobs/{job_id}/resumes",
        files={"files": ("cv.txt", b"Jane Roe python", "text/plain")},
    )
    task_id = upload.json()[0]["task_id"]
    resp = await auth_client.get(f"/api/v1/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["task_type"] == "resume_parse"
