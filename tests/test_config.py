import os
from unittest.mock import patch

import pytest

from modules.intelligence.gemini_agent import GeminiFlash
from modules.sources.binance_client import BinanceSync


def test_missing_env_variables():
    """Test that missing API keys do not crash the initialization."""
    with patch.dict(os.environ, {}, clear=True):  # Simulates an empty .env file
        # Binance should handle missing keys gracefully (might raise an internal error but shouldn't crash the OS)
        try:
            binance = BinanceSync()
            holdings = binance.fetch_holdings()
            assert holdings == []  # Should return empty list on auth failure
        except Exception as e:
            pytest.fail(f"BinanceSync crashed on missing env vars: {e}")

        # Gemini should disable itself and return the fallback response
        gemini = GeminiFlash()
        assert gemini.client is None

        fallback = gemini.analyze_briefing("Test news")
        assert fallback['market_vibe'] == "AI Features Offline (Check .env)"
        assert fallback['global_score'] == 0.0


def test_gemini_rate_limit_handling():
    """Test that HTTP 429 Resource Exhausted is handled securely."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
        gemini = GeminiFlash()

        # Mock the client to raise an exception simulating a 429 error
        with patch.object(gemini, 'client') as mock_client:
            mock_client.models.generate_content.side_effect = Exception("429 Resource Exhausted")

            response = gemini.analyze_briefing("Market is crashing")
            assert "AI Processing Failed" in response['market_vibe'] or "fallback" in str(response).lower()
