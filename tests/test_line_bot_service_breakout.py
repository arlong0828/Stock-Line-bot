from pathlib import Path
import sys
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.lineBotService import LineBotService


@pytest.mark.anyio
async def test_handle_breakout_analysis_returns_report():
    fake_db = object()
    service = LineBotService(fake_db)
    service.breakoutService.getBreakoutReport = AsyncMock(return_value="mock report")

    result = await service.handleBreakoutAnalysis(limit=3)

    assert result == "mock report"
    service.breakoutService.getBreakoutReport.assert_awaited_once_with(limit=3)
