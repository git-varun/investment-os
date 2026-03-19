import logging

import pandas as pd
import yfinance as yf


class QuantEngine:
    """Calculates Technical Indicators (RSI, ATR, SMA) for precise Entry/Exits."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._cache = {}

    def analyze_asset(self, symbol: str, current_price: float) -> dict:
        # 1. Return cached data if already calculated this session
        if symbol in self._cache:
            return self._cache[symbol]

        # Default metrics if math fails or asset is manual (e.g., FD)
        metrics = {"rsi": None, "atr": None, "sma_50": None, "tsl": None, "math_signal": "HOLD"}

        if symbol == "GOLD" or symbol.startswith("FD-"):
            return metrics

        try:
            # 2. Fetch 6 months of daily OHLCV data
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if df.empty or len(df) < 50:
                return metrics

            # Fix multi-index columns for yfinance 2026 update
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 3. Calculate Indicators using pandas-ta
            df.ta.rsi(length=14, append=True)
            df.ta.atr(length=14, append=True)
            df.ta.sma(length=50, append=True)

            latest = df.iloc[-1]
            rsi = float(latest.get('RSI_14', 50))
            atr = float(latest.get('ATRr_14', 0))
            sma_50 = float(latest.get('SMA_50', current_price))

            # 4. Mathematically Perfect Trailing Stop Loss (Price - 2x Volatility)
            tsl = current_price - (2 * atr) if atr else (current_price * 0.95)

            # 5. Generate Raw Math Signals (To be combined with News later)
            signal = "HOLD"
            if rsi < 30 and current_price < sma_50:
                signal = "AVG DOWN"  # Oversold and cheap
            elif rsi > 70:
                signal = "TAKE PROFIT"  # Overbought, lock in gains
            elif current_price < tsl:
                signal = "SELL (TSL HIT)"

            metrics = {
                "rsi": round(rsi, 2),
                "atr": round(atr, 2),
                "sma_50": round(sma_50, 2),
                "tsl": round(tsl, 2),
                "math_signal": signal
            }

            self._cache[symbol] = metrics
            return metrics

        except Exception as e:
            self.logger.debug(f"Quant calculation failed for {symbol}: {e}")
            return metrics
