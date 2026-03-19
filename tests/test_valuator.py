import pytest

from modules.common.valuator import PortfolioValuator
from modules.interfaces import PriceProvider


class DummyPricer(PriceProvider):
    """A mock price provider that always returns 100.0 for testing."""

    def get_price(self, symbol: str, asset_type: str):
        return 100.0


@pytest.fixture
def valuator():
    # Inject our DummyPricer instead of YFinance/Binance
    return PortfolioValuator(pricers=[DummyPricer()])


def test_fixed_income_pricing(valuator):
    """FDs and Cash should always be exactly 1:1, overriding APIs."""
    asset = {"symbol": "FD-SBI", "qty": 50000, "type": "fixed_income"}
    price = valuator.get_price(asset)
    assert price == 1.0


def test_crypto_usd_conversion(valuator, mocker):
    """Ensures crypto priced in USD gets multiplied by the FX rate."""
    mocker.patch.object(valuator, 'get_live_fx', return_value=85.0)  # Mock USD/INR rate to 85

    # DummyPricer returns 100 USD for BTC. Value should be 100 * 85 = 8500 INR per unit
    assets = [{"symbol": "BTC-USD", "qty": 2.0, "type": "crypto"}]
    total = valuator.calculate_total(assets)

    # 2.0 qty * 100 USD price * 85 INR fx rate = 17000
    assert total == 17000.0


def test_gold_pricing(valuator, mocker):
    """Ensures the Troy Ounce to Gram conversion math is accurate."""
    mocker.patch.object(valuator, 'get_live_fx', return_value=80.0)
    # Mock yfinance inside get_price for Gold specifically
    mocker.patch('yfinance.Ticker.fast_info', new_callable=mocker.PropertyMock, return_value={'last_price': 2000.0})

    asset = {"symbol": "GOLD", "qty": 10, "type": "commodity"}
    price = valuator.get_price(asset)

    # (2000 USD * 80 INR) / 31.1034768 grams = 5144.12
    assert round(price, 2) == 5144.12
