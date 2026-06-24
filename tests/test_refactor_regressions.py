import importlib
import importlib.util
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException


@pytest.fixture(scope="module")
def ext_modules():
    root = Path(__file__).resolve().parents[1]

    if "ext_scheduler" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "ext_scheduler",
            root / "__init__.py",
            submodule_search_locations=[str(root)],
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules["ext_scheduler"] = module
        spec.loader.exec_module(module)

    crud = importlib.import_module("ext_scheduler.crud")
    models = importlib.import_module("ext_scheduler.models")
    views_api = importlib.import_module("ext_scheduler.views_api")
    return crud, models, views_api


def _sample_job(models, **overrides):
    data = {
        "id": "job123",
        "name": "test job",
        "admin": "admin123",
        "status": True,
        "schedule": "*/5 * * * *",
        "selectedverb": "GET",
        "url": "https://example.com",
        "headers": [],
        "body": "{}",
        "extra": {},
    }
    data.update(overrides)
    return models.Job(**data)


@pytest.mark.asyncio
async def test_update_scheduler_job_rejects_missing_url(ext_modules, monkeypatch):
    crud, models, _ = ext_modules
    job = _sample_job(models, url=None)

    execute_mock = AsyncMock()
    monkeypatch.setattr(crud.db, "execute", execute_mock)

    with pytest.raises(ValueError, match="URL is required"):
        await crud.update_scheduler_job(job)

    execute_mock.assert_not_called()


@pytest.mark.asyncio
async def test_update_scheduler_job_rejects_invalid_schedule(ext_modules, monkeypatch):
    crud, models, _ = ext_modules
    job = _sample_job(models, schedule="not a cron")

    monkeypatch.setattr(crud, "validate_cron_string", AsyncMock(return_value=False))
    execute_mock = AsyncMock()
    monkeypatch.setattr(crud.db, "execute", execute_mock)

    with pytest.raises(ValueError, match="Invalid cron schedule format"):
        await crud.update_scheduler_job(job)

    execute_mock.assert_not_called()


@pytest.mark.asyncio
async def test_update_scheduler_job_uses_trimmed_schedule(ext_modules, monkeypatch):
    crud, models, _ = ext_modules
    job = _sample_job(models, schedule="  */10 * * * *  ", status=True)

    monkeypatch.setattr(crud, "validate_cron_string", AsyncMock(return_value=True))
    db_execute = AsyncMock()
    monkeypatch.setattr(crud.db, "execute", db_execute)
    add_job_mock = AsyncMock()
    monkeypatch.setattr(crud, "add_job", add_job_mock)
    monkeypatch.setattr(crud, "get_scheduler_job", AsyncMock(return_value=job))

    await crud.update_scheduler_job(job)

    assert db_execute.await_args is not None
    assert db_execute.await_args.args[1]["schedule"] == "*/10 * * * *"
    assert add_job_mock.await_args is not None
    assert add_job_mock.await_args.kwargs["cron_expr"] == "*/10 * * * *"


@pytest.mark.asyncio
async def test_api_scheduler_pause_returns_500_when_pause_fails(
    ext_modules, monkeypatch
):
    _, models, views_api = ext_modules
    job = _sample_job(models)

    monkeypatch.setattr(views_api, "get_scheduler_job", AsyncMock(return_value=job))
    monkeypatch.setattr(views_api, "pause_scheduler", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc:
        await views_api.api_scheduler_pause(job.id, "true")

    assert exc.value.status_code == 500
    assert "Failed to update scheduler job state" in exc.value.detail


@pytest.mark.asyncio
async def test_api_scheduler_pause_returns_404_when_job_missing(
    ext_modules, monkeypatch
):
    _, _, views_api = ext_modules
    monkeypatch.setattr(views_api, "get_scheduler_job", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc:
        await views_api.api_scheduler_pause("missing-job", "true")

    assert exc.value.status_code == 404
