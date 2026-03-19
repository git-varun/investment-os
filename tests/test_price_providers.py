from unittest.mock import patch, MagicMock

from modules.common.notifier import Notifier
from modules.common.price_providers import (
    BinancePricer,
    CoinGeckoPricer,
    CoinMarketCapPricer,
    YFinancePricer,
    GoogleFinanceScraperPricer
)
from modules.intelligence.news_providers import GoogleNews, YahooFinanceNews


@patch('os.getenv')
@patch('requests.post')
def test_notifier_success(mock_post, mock_getenv):
    # Mock env vars
    mock_getenv.side_effect = lambda \
        k: "fake-token" if k == "TELEGRAM_BOT_TOKEN" else "fake-chat-id" if k == "TELEGRAM_CHAT_ID" else None

    # Mock successful response
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_post.return_value = mock_res

    notifier = Notifier()
    notifier.send_telegram("Hello Test")

    assert mock_post.called
    args, kwargs = mock_post.call_args
    assert "fake-token" in args[0]
    assert kwargs['json']['chat_id'] == "fake-chat-id"
    assert kwargs['json']['text'] == "Hello Test"


@patch('os.getenv')
@patch('requests.post')
def test_notifier_missing_config(mock_post, mock_getenv):
    # Mock missing env vars
    mock_getenv.return_value = None

    notifier = Notifier()
    notifier.send_telegram("Hello Test")

    assert not mock_post.called


@patch('requests.get')
def test_binance_pricer_success(mock_get):
    # Mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"symbol": "BTCUSDT", "price": "65000.50"}
    mock_get.return_value = mock_response

    pricer = BinancePricer()
    price = pricer.get_price("BTC-USD", "crypto")

    assert price == 65000.50
    mock_get.assert_called_once_with("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)


@patch('requests.get')
def test_binance_pricer_failure(mock_get):
    mock_get.side_effect = Exception("API Down")

    pricer = BinancePricer()
    price = pricer.get_price("BTC-USD", "crypto")

    assert price is None


@patch('requests.get')
def test_coingecko_pricer_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"bitcoin": {"usd": 64000.0}}
    mock_get.return_value = mock_response

    pricer = CoinGeckoPricer()
    price = pricer.get_price("BTC-USD", "crypto")

    assert price == 64000.0
    mock_get.assert_called_once_with("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
                                     timeout=5)


@patch('os.getenv')
@patch('requests.get')
def test_coinmarketcap_pricer_success(mock_get, mock_getenv):
    mock_getenv.return_value = "fake-api-key"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "BTC": [
                {
                    "quote": {
                        "USD": {
                            "price": 63000.25
                        }
                    }
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    pricer = CoinMarketCapPricer()
    price = pricer.get_price("BTC-USD", "crypto")

    assert price == 63000.25
    headers = {'X-CMC_PRO_API_KEY': 'fake-api-key'}
    params = {'symbol': 'BTC', 'convert': 'USD'}
    mock_get.assert_called_once_with("https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest",
                                     headers=headers, params=params, timeout=5)


@patch('os.getenv')
def test_coinmarketcap_pricer_no_key(mock_getenv):
    mock_getenv.return_value = None
    pricer = CoinMarketCapPricer()
    price = pricer.get_price("BTC-USD", "crypto")
    assert price is None


@patch('yfinance.Ticker')
def test_yfinance_pricer_success(mock_ticker):
    mock_instance = MagicMock()
    mock_instance.fast_info = {'last_price': 2500.5}
    mock_ticker.return_value = mock_instance

    pricer = YFinancePricer()
    price = pricer.get_price("RELIANCE.NS", "stock")

    assert price == 2500.5
    mock_ticker.assert_called_once_with("RELIANCE.NS")


@patch('requests.get')
def test_google_finance_scraper_success(mock_get):
    mock_response = MagicMock()
    mock_response.text = '<html><body><div class="YMlKec fxKbKc">₹2,450.75</div></body></html>'
    mock_get.return_value = mock_response

    pricer = GoogleFinanceScraperPricer()
    price = pricer.get_price("RELIANCE.NS", "stock")

    assert price == 2450.75
    mock_get.assert_called_once_with("https://www.google.com/finance/quote/RELIANCE:NSE", timeout=5)


@patch('requests.get')
def test_google_finance_scraper_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.text = '<html><body><div>No price here</div></body></html>'
    mock_get.return_value = mock_response

    pricer = GoogleFinanceScraperPricer()
    price = pricer.get_price("RELIANCE.NS", "stock")

    assert price is None


@patch('feedparser.parse')
def test_google_news_success(mock_parse):
    mock_feed = MagicMock()
    mock_entry1 = MagicMock()
    mock_entry1.title = "News 1"
    mock_entry2 = MagicMock()
    mock_entry2.title = "News 2"
    mock_feed.entries = [mock_entry1, mock_entry2]
    mock_parse.return_value = mock_feed

    news = GoogleNews()
    headlines = news.fetch_headlines("RELIANCE.NS")

    assert headlines == "News 1 | News 2"
    assert mock_parse.called


@patch('feedparser.parse')
def test_yahoo_news_success(mock_parse):
    mock_feed = MagicMock()
    mock_entry1 = MagicMock()
    mock_entry1.title = "Yahoo 1"
    mock_feed.entries = [mock_entry1]
    mock_parse.return_value = mock_feed

    news = YahooFinanceNews()
    headlines = news.fetch_headlines("AAPL")

    assert headlines == "Yahoo 1"
    assert mock_parse.called
