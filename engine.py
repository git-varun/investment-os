import concurrent.futures
import logging
from typing import List

from modules.common.notifier import Notifier
from modules.common.price_providers import (
    BinancePricer, CoinGeckoPricer, CoinMarketCapPricer, YFinancePricer, GoogleFinanceScraperPricer
)
from modules.common.valuator import PortfolioValuator
from modules.intelligence.gemini_agent import GeminiFlash
from modules.intelligence.memory_engine import MemoryEngine
from modules.intelligence.news_engine import NewsEngine
from modules.intelligence.news_providers import GoogleNews, YahooFinanceNews
from modules.intelligence.portfolio_math import PortfolioAnalytics
from modules.intelligence.quant_engine import QuantEngine
from modules.interfaces import AssetSource, AIModel
from modules.sources.binance_client import BinanceSync
from modules.sources.groww_client import GrowwSync
from modules.sources.local_client import LocalAssetSync


class InvestmentEngine:
    def __init__(self):
        self.logger = logging.getLogger("Engine")
        # 1. Register Asset Plugins
        self.sources: List[AssetSource] = [
            GrowwSync(),
            BinanceSync(),
            LocalAssetSync()
        ]

        # 2. Register News Plugins (Priority Order)
        active_news_providers = [GoogleNews(), YahooFinanceNews()]
        self.news_hub = NewsEngine(active_news_providers)

        # 3. Register Price Plugins (Priority Order: Fastest/Most Reliable first)
        active_price_providers = [
            BinancePricer(),  # Best for Crypto
            YFinancePricer(),  # Best for Stocks
            CoinGeckoPricer(),  # Crypto Fallback 1
            CoinMarketCapPricer(),  # Crypto Fallback 2 (if key exists)
            GoogleFinanceScraperPricer()  # Stock Fallback 1
        ]

        # 4. Register Intelligence & Tools
        self.ai_brain: AIModel = GeminiFlash()
        self.valuator = PortfolioValuator(active_price_providers)
        self.bot = Notifier()
        self.quant = QuantEngine()
        self.portfolio_math = PortfolioAnalytics()
        self.memory = MemoryEngine()
        # Run memory consolidation on startup (calculates past impacts)
        self.memory.consolidate_memories()
        self.last_analysis = None

    def sync_portfolio(self):
        self.logger.info("📡 Stage 1/3: Syncing raw assets from all broker plugins...")
        all_holdings = []
        for source in self.sources:
            try:
                self.logger.debug(f"Fetching from {type(source).__name__}...")
                holdings = source.fetch_holdings()
                all_holdings.extend(holdings)
            except Exception as e:
                self.logger.error(f"⚠️ Source Failure {type(source).__name__}: {e}")
        self.logger.info(f"✅ Found {len(all_holdings)} assets across {len(self.sources)} sources.")
        return all_holdings

    def calculate_global_score(self, assets, ai_response):
        """Quant Math: Weighted Average of Sentiment by Capital Allocation."""
        if not ai_response: return 0.0

        total_val = sum(a.get('value_inr', 0) for a in assets)
        if total_val == 0: return 0.0

        # We apply the AI's 'global_score' to the weighted value of the top 5 assets
        weighted_score = 0.0
        top_assets = sorted(assets, key=lambda x: x.get('value_inr', 0), reverse=True)[:5]

        for a in top_assets:
            weight = a.get('value_inr', 0) / total_val
            weighted_score += (ai_response.get('global_score', 0) * weight)

        return round(weighted_score, 2)

    def enrich_portfolio(self, assets):
        self.logger.info("🧮 Stage 2/3: Fetching Live Prices (Multithreaded)...")
        total_inr = 0.0
        fx_rate = self.valuator.get_live_fx()

        # Simple mapping to give assets clean names for the table
        def get_name(sym):
            mapping = {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin",
                       "RELIANCE.NS": "Reliance Ind.", "ZOMATO.NS": "Zomato Ltd", "GOLD": "Physical Gold"}
            return mapping.get(sym, sym.split('.')[0].replace('-USD', ''))

        def process_asset(a):
            price = self.valuator.get_price(a)
            a['live_price'] = price
            a['name'] = get_name(a['symbol'])  # <-- Added friendly name

            if "-USD" in a['symbol'] or a.get('type') == 'crypto':
                a['value_inr'] = price * a['qty'] * fx_rate
            else:
                a['value_inr'] = price * a['qty']

            quant_data = self.quant.analyze_asset(a['symbol'], price)
            a.update(quant_data)
            return a

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            enriched_assets = list(executor.map(process_asset, assets))

        for a in enriched_assets:
            total_inr += a.get('value_inr', 0)

        # Return the fx_rate too so we can print it in the Audit log
        return enriched_assets, total_inr, fx_rate

    def generate_alpha_briefing(self, assets, total_inr):
        self.logger.info("🧠 Stage 3/3: Bundling Macro, News, and Requesting AI Strategy...")

        health = self.portfolio_math.analyze_health(assets, total_inr)

        # 🌍 NEW: Fetch Global Macro Indicators
        try:
            import yfinance as yf
            import pandas as pd
            # BZ=F (Brent Crude), ^TNX (US 10Y Yield), ^INDIAVIX (India Volatility)
            macro_df = yf.download("BZ=F ^TNX ^INDIAVIX", period="1d", progress=False)['Close']
            if isinstance(macro_df.columns, pd.MultiIndex):
                macro_df.columns = macro_df.columns.get_level_values(0)

            brent = f"${macro_df.get('BZ=F', [0]).iloc[-1]:.2f}"
            us_10y = f"{macro_df.get('^TNX', [0]).iloc[-1]:.2f}%"
            india_vix = f"{macro_df.get('^INDIAVIX', [0]).iloc[-1]:.2f}"
            macro_string = f"Brent Crude: {brent} | US 10Y Yield: {us_10y} | India VIX: {india_vix}"
        except Exception:
            macro_string = "Real-time Macro Data Unavailable."

        # Build the Institutional Intel Bundle
        intel_bundle = f"GLOBAL MACRO INDICATORS:\n{macro_string}\n\n"
        intel_bundle += f"MACRO PORTFOLIO RISK:\n"
        intel_bundle += f"- Asset Allocation: {health.get('allocation', {})}\n"
        intel_bundle += f"- Portfolio Beta: {health.get('beta', 1.0)}\n\n"

        top_assets = sorted(assets, key=lambda x: x.get('value_inr', 0), reverse=True)[:15]

        def fetch_news(asset):
            return asset['symbol'], self.news_hub.fetch_headlines(asset['symbol'])

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            news_results = dict(executor.map(fetch_news, top_assets))

        for asset in top_assets:
            symbol = asset['symbol']
            price = asset.get('live_price', 0)
            headlines = news_results.get(symbol, "")

            self.memory.log_today_news(symbol, headlines, price)
            past_context = self.memory.recall_history(symbol)

            intel_bundle += f"\n[{symbol}] Price: {price} | RSI: {asset.get('rsi', 'N/A')}\nToday's News: {headlines}\n"
            if past_context: intel_bundle += f"{past_context}\n"

        if len(top_assets) > 0:
            # 📤 LOG FULL PAYLOAD SENT TO GEMINI
            self.logger.info(f"📤 SENDING TO GEMINI:\n{intel_bundle}")
            self.last_analysis = self.ai_brain.analyze_briefing(intel_bundle)
            return self.last_analysis

        return None
