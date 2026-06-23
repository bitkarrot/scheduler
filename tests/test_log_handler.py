import pytest

from helpers import get_complete_log


@pytest.mark.asyncio
async def test_get_complete_log_when_missing_file():
    # Ensure helper returns a string either way and does not crash.
    output = await get_complete_log()
    assert isinstance(output, str)


@pytest.mark.asyncio
async def test_get_complete_log_reads_content(tmp_path, monkeypatch):
    test_log = tmp_path / "scheduler.log"
    test_log.write_text("line1\nline2\n", encoding="utf-8")

    import helpers

    monkeypatch.setattr(helpers, "log_path", str(test_log))

    output = await get_complete_log()
    assert "line1" in output
    assert "line2" in output
