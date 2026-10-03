from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.stockData import StockInfo
from app.database.session import AsyncSessionLocal


@dataclass
class BreakoutCandidate:
    symbol: str
    name: str
    close_price: float
    day_change_pct: float
    breakout_pct: float
    volume_ratio: float
    score: float


class BreakoutService:
    def rankBreakoutCandidates(self, stocks: Iterable, limit: int = 5) -> list[BreakoutCandidate]:
        candidates: list[BreakoutCandidate] = []

        for stock in stocks:
            if getattr(stock, "is_etf", False):
                continue

            histories = sorted(getattr(stock, "histories", []), key=lambda row: row.date)
            if len(histories) < 25:
                continue

            recent = histories[-25:]
            latest = recent[-1]
            previous = recent[-2]
            prior_window = recent[-21:-1]
            if not prior_window:
                continue

            prior_high = max((row.high_price or row.close_price or 0) for row in prior_window)
            latest_close = float(latest.close_price or 0)
            previous_close = float(previous.close_price or 0)
            latest_volume = float(latest.volume or 0)
            avg_volume_20 = mean(float(row.volume or 0) for row in prior_window)

            if prior_high <= 0 or previous_close <= 0 or avg_volume_20 <= 0:
                continue

            breakout_pct = (latest_close - prior_high) / prior_high * 100
            day_change_pct = (latest_close - previous_close) / previous_close * 100
            volume_ratio = latest_volume / avg_volume_20

            if breakout_pct <= 0:
                continue
            if day_change_pct < 3:
                continue
            if volume_ratio < 1.5:
                continue

            score = breakout_pct * 3 + day_change_pct * 2 + volume_ratio * 8
            candidates.append(
                BreakoutCandidate(
                    symbol=stock.symbol,
                    name=stock.name,
                    close_price=latest_close,
                    day_change_pct=day_change_pct,
                    breakout_pct=breakout_pct,
                    volume_ratio=volume_ratio,
                    score=score,
                )
            )

        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates[:limit]

    def formatBreakoutReport(self, candidates: list[BreakoutCandidate]) -> str:
        if not candidates:
            return "⚠️ 目前資料庫裡沒有符合條件的飆股候選。\n請先用「加入股票 2330 3037 ...」累積歷史資料後再試一次。"

        lines = ["🚀 飆股候選", ""]
        for index, candidate in enumerate(candidates, start=1):
            lines.append(
                f"{index}. {candidate.symbol} {candidate.name}\n"
                f"   收盤: {candidate.close_price:.2f}\n"
                f"   單日漲幅: {candidate.day_change_pct:+.2f}%\n"
                f"   突破幅度: {candidate.breakout_pct:+.2f}%\n"
                f"   量比: {candidate.volume_ratio:.2f}x"
            )
        lines.append("")
        lines.append("規則：排除 ETF，抓 20 日新高突破 + 當日漲幅 > 3% + 爆量。")
        return "\n".join(lines)

    async def getBreakoutReport(self, limit: int = 5) -> str:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(StockInfo).options(selectinload(StockInfo.histories))
            )
            stocks = result.scalars().all()

        candidates = self.rankBreakoutCandidates(stocks, limit=limit)
        return self.formatBreakoutReport(candidates)


breakoutService = BreakoutService()
