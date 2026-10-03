from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import twstock
from app.services import stockCrawler  # noqa: F401  # trigger module import side effects


def test_stock_crawler_does_not_break_twstock_datatuple_shape():
    assert twstock.stock.DATATUPLE._fields == (
        "date",
        "capacity",
        "turnover",
        "open",
        "high",
        "low",
        "close",
        "change",
        "transaction",
        "note",
    )
