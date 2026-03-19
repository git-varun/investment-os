from unittest.mock import MagicMock, patch

from engine import InvestmentEngine


@patch('engine.MemoryEngine')  # <-- THIS PREVENTS SQLITE CRASHES DURING TESTS
def test_full_pipeline_sync_to_enrich(MockMemoryEngine):
    """Tests the data flow from fetching holdings to enriching them with math."""
    engine = InvestmentEngine()

    # 1. Mock Sources (So we don't hit real brokerages)
    mock_source = MagicMock()
    mock_source.fetch_holdings.return_value = [{"symbol": "MOCK-STOCK", "qty": 10, "type": "stock", "source": "mock"}]
    engine.sources = [mock_source]

    # 2. Mock Valuator
    engine.valuator.get_price = MagicMock(return_value=150.0)
    engine.valuator.get_live_fx = MagicMock(return_value=1.0)

    # 3. Mock Quant Engine
    engine.quant.analyze_asset = MagicMock(return_value={"rsi": 45, "math_signal": "HOLD", "tsl": 140.0})

    # Execute Pipeline
    raw_assets = engine.sync_portfolio()
    enriched_assets, total_val, fx = engine.enrich_portfolio(raw_assets)

    # Assertions
    assert len(enriched_assets) == 1
    asset = enriched_assets[0]

    # Check Math Integration
    assert total_val == 1500.0  # 10 qty * 150 price
    assert asset['value_inr'] == 1500.0
    assert asset['rsi'] == 45
    assert asset['tsl'] == 140.0
    assert asset['math_signal'] == "HOLD"


def test_memory_engine_sqlite_isolation():
    """Ensures MemoryEngine can create a DB, log, and recall without failing."""
    from modules.intelligence.memory_engine import MemoryEngine
    import tempfile

    # Use a temporary SQLite file so we don't pollute real data
    with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as tmp:
        memory = MemoryEngine(db_path=tmp.name)

        # Test Logging
        memory.log_today_news("TEST-SYM", "Company announces record profits", 100.0)

        # Test Recall (should be empty initially because it's not resolved/T+3 yet)
        recall = memory.recall_history("TEST-SYM")
        assert recall == ""
