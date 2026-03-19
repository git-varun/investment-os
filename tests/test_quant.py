import pandas as pd
import pytest

from modules.intelligence.portfolio_math import PortfolioAnalytics
from modules.intelligence.quant_engine import QuantEngine


@pytest.fixture
def dummy_market_data():
    """Generates 60 days of fake stock data for pandas-ta."""
    dates = pd.date_range(start='2026-01-01', periods=60, freq='D')
    return pd.DataFrame({
        'Open': [100] * 60,
        'High': [105] * 60,
        'Low': [95] * 60,
        'Close': [102] * 60,  # Flat market
        'Volume': [1000] * 60
    }, index=dates)


def test_quant_engine_standard(mocker, dummy_market_data):
    """Test RSI, ATR, TSL math on standard data."""
    mocker.patch('yfinance.download', return_value=dummy_market_data)

    quant = QuantEngine()
    metrics = quant.analyze_asset("RELIANCE.NS", 102.0)

    assert metrics['rsi'] is not None
    assert metrics['tsl'] < 102.0  # Trailing Stop Loss should be BELOW current price
    assert metrics['math_signal'] in ["HOLD", "AVG DOWN", "TAKE PROFIT", "SELL (TSL HIT)"]


def test_portfolio_allocation_math():
    """Test macro asset allocation percentages."""
    assets = [
        {"symbol": "RELIANCE", "type": "stock", "value_inr": 60000},
        {"symbol": "BTC-USD", "type": "crypto", "value_inr": 30000},
        {"symbol": "FD", "type": "fixed_income", "value_inr": 10000}
    ]
    total_val = 100000

    math_engine = PortfolioAnalytics()
    health = math_engine.analyze_health(assets, total_val)

    assert health['allocation']['STOCK'] == 60.0
    assert health['allocation']['CRYPTO'] == 30.0
    assert health['allocation']['FIXED_INCOME'] == 10.0
