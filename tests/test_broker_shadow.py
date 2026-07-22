"""
Shadow account tests — CSV parsing, analysis, and tool registration.
"""

from __future__ import annotations

import pytest
from agent.broker.shadow import parse_trades_csv, analyze_trades, ImportedTrade


SAMPLE_CSV = """symbol,side,qty,price,commission,realized_pl,timestamp
AAPL,buy,10,150.0,1.0,,
AAPL,sell,10,160.0,1.0,100.0,
MSFT,buy,5,300.0,0.5,,
MSFT,sell,5,310.0,0.5,50.0,
TSLA,buy,20,200.0,2.0,,
TSLA,sell,20,180.0,2.0,-400.0,
"""


class TestParseTradesCSV:
    def test_parse_valid_csv(self):
        trades = parse_trades_csv(SAMPLE_CSV)
        assert len(trades) == 6
        assert trades[0].symbol == "AAPL"
        assert trades[0].side == "buy"
        assert trades[1].realized_pl == 100.0

    def test_parse_minimal_csv(self):
        csv_content = "symbol,side,qty,price\nAAPL,buy,10,150.0\n"
        trades = parse_trades_csv(csv_content)
        assert len(trades) == 1
        assert trades[0].price == 150.0
        assert trades[0].commission is None

    def test_parse_empty_csv(self):
        trades = parse_trades_csv("")
        assert trades == []

    def test_parse_header_only(self):
        trades = parse_trades_csv("symbol,side,qty,price")
        assert trades == []

    def test_parse_missing_columns(self):
        trades = parse_trades_csv("a,b,c\nd,e,f")
        assert trades == []

    def test_parse_skips_bad_rows(self):
        csv_content = "symbol,side,qty,price\nAAPL,buy,10,150.0\nBAD_ROW\nMSFT,sell,not_a_number,300.0"
        trades = parse_trades_csv(csv_content)
        assert len(trades) == 1  # only the valid row


class TestAnalyzeTrades:
    def test_empty_trades(self):
        analysis = analyze_trades([])
        assert analysis.total_trades == 0
        assert analysis.win_rate == 0.0

    def test_all_winners(self):
        trades = [
            ImportedTrade(symbol="AAPL", side="sell", qty=10, price=160, realized_pl=100),
            ImportedTrade(symbol="MSFT", side="sell", qty=5, price=310, realized_pl=50),
        ]
        analysis = analyze_trades(trades)
        assert analysis.total_trades == 2
        assert analysis.winning_trades == 2
        assert analysis.win_rate == 1.0
        assert analysis.total_pl == 150.0

    def test_mixed_results(self):
        trades = [
            ImportedTrade(symbol="AAPL", side="sell", qty=10, price=160, realized_pl=100),
            ImportedTrade(symbol="TSLA", side="sell", qty=20, price=180, realized_pl=-50),
        ]
        analysis = analyze_trades(trades)
        assert analysis.total_trades == 2
        assert analysis.winning_trades == 1
        assert analysis.losing_trades == 1
        assert analysis.win_rate == 0.5
        assert analysis.total_pl == 50.0

    def test_symbol_breakdown(self):
        trades = [
            ImportedTrade(symbol="AAPL", side="sell", qty=10, price=160, realized_pl=100),
            ImportedTrade(symbol="AAPL", side="sell", qty=5, price=170, realized_pl=50),
            ImportedTrade(symbol="MSFT", side="sell", qty=5, price=310, realized_pl=50),
        ]
        analysis = analyze_trades(trades)
        assert "AAPL" in analysis.symbol_breakdown
        assert "MSFT" in analysis.symbol_breakdown
        assert analysis.symbol_breakdown["AAPL"]["trades"] == 2
        assert analysis.symbol_breakdown["AAPL"]["total_pl"] == 150.0

    def test_max_win_max_loss(self):
        trades = [
            ImportedTrade(symbol="A", side="sell", qty=1, price=100, realized_pl=200),
            ImportedTrade(symbol="B", side="sell", qty=1, price=100, realized_pl=-300),
        ]
        analysis = analyze_trades(trades)
        assert analysis.max_win == 200.0
        assert analysis.max_loss == -300.0

    def test_to_dict_structure(self):
        trades = [ImportedTrade(symbol="AAPL", side="sell", qty=10, price=160, realized_pl=100)]
        analysis = analyze_trades(trades)
        d = analysis.to_dict()
        assert "total_trades" in d
        assert "win_rate" in d
        assert "symbol_breakdown" in d
