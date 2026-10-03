from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.breakoutService import BreakoutService


@dataclass
class FakeHistory:
    date: date
    close_price: float
    high_price: float
    volume: int


@dataclass
class FakeStock:
    symbol: str
    name: str
    is_etf: bool
    histories: list[FakeHistory]


def make_histories(closes: list[float], volumes: list[int]) -> list[FakeHistory]:
    start = date(2026, 1, 1)
    rows = []
    for i, (close, volume) in enumerate(zip(closes, volumes)):
        rows.append(
            FakeHistory(
                date=start + timedelta(days=i),
                close_price=close,
                high_price=close,
                volume=volume,
            )
        )
    return rows


def test_identifies_breakout_candidates_and_ranks_them():
    service = BreakoutService()

    strong = FakeStock(
        symbol="9999",
        name="強勢股",
        is_etf=False,
        histories=make_histories(
            [50] * 20 + [51, 52, 54, 57, 63],
            [1000] * 20 + [1200, 1300, 1600, 2200, 5200],
        ),
    )
    weaker = FakeStock(
        symbol="8888",
        name="次強勢股",
        is_etf=False,
        histories=make_histories(
            [30] * 20 + [30.5, 31, 31.5, 32, 33],
            [900] * 20 + [950, 980, 1000, 1200, 2100],
        ),
    )

    candidates = service.rankBreakoutCandidates([strong, weaker], limit=5)

    assert [candidate.symbol for candidate in candidates] == ["9999", "8888"]
    assert candidates[0].score > candidates[1].score
    assert candidates[0].volume_ratio > 2
    assert candidates[0].breakout_pct > 0


def test_excludes_etfs_and_non_breakouts():
    service = BreakoutService()

    etf = FakeStock(
        symbol="0050",
        name="ETF",
        is_etf=True,
        histories=make_histories(
            [100] * 20 + [101, 102, 103, 104, 105],
            [5000] * 25,
        ),
    )
    flat = FakeStock(
        symbol="7777",
        name="盤整股",
        is_etf=False,
        histories=make_histories(
            [40] * 25,
            [1000] * 25,
        ),
    )

    candidates = service.rankBreakoutCandidates([etf, flat], limit=5)

    assert candidates == []


def test_formats_human_readable_breakout_report():
    service = BreakoutService()
    stock = FakeStock(
        symbol="9999",
        name="強勢股",
        is_etf=False,
        histories=make_histories(
            [50] * 20 + [51, 52, 54, 57, 63],
            [1000] * 20 + [1200, 1300, 1600, 2200, 5200],
        ),
    )

    candidates = service.rankBreakoutCandidates([stock], limit=3)
    message = service.formatBreakoutReport(candidates)

    assert "飆股候選" in message
    assert "9999 強勢股" in message
    assert "量比" in message
