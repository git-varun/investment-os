import json
import logging
import os

from google import genai

from modules.interfaces import AIModel


class GeminiFlash(AIModel):
    def __init__(self):
        self.logger = logging.getLogger("Gemini")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.logger.warning("GEMINI_API_KEY not found. AI disabled.")
            self.client = None
            return

        try:
            self.client = genai.Client(api_key=api_key)
            self.model_id = "gemini-3.1-flash-lite-preview"
        except Exception as e:
            self.logger.error(f"SDK Init Failed: {e}")
            self.client = None

    def analyze_briefing(self, context: str):
        if not self.client:
            return self._fallback_response("AI Features Offline (Check .env)")

        prompt = f"""
            Role: You are a Multi-Strategy Portfolio Manager. Your objective is to perform a 3-tier analysis (Macro, Fundamental, and Technical) on the provided portfolio, looking for inter-asset correlations and global catalysts.
    
            Phase 1: Macro & Global Synthesis
            - Global Events: Analyze how current global events (Geopolitics, Fed/RBI Interest Rate changes, Brent Crude prices, US Bond Yields) impact Indian Equities and Crypto.
            - Sentiment Scouring: Determine if the current "Market Vibe" is Risk-On or Risk-Off.
            - Announcement Impact: Review the provided corporate announcements for systemic risk.
    
            Phase 2: The Correlation Matrix (Cross-Check)
            - Sector Contagion: If one stock in a sector is failing due to macro news, apply that risk weight to all other correlated assets.
            - Equity-Crypto Inverse: Note if FIIs are moving from Emerging Markets into "Safe Haven" assets.
            - Dependency Check: Identify correlations (e.g., Rising Crude = Negative for Paints/Aviation, Positive for Energy).
    
            Phase 3: Triple-Technical Analysis
            For every asset, justify your "Action" using these three pillars:
            - Technical: Use provided RSI and EMA data. Identify Overbought (>70) or Oversold (<30) conditions.
            - Fundamental: Evaluate the "Why" behind the price move using the news.
            - Market Structure: Analyze if the move is "Technical Selling" or "Structural Decay".
    
            DATA BUNDLE:
            {context}
    
            Output Requirements:
            Return ONLY a raw JSON payload with this strict schema:
            {{
                "market_vibe": "A 2-sentence 'Executive Summary' of the Global Market Pulse.",
                "macro_analysis": "Deep analysis of sector contagion, correlations, and macro impacts.",
                "global_score": 0.5,
                "confidence_score": 0.85,
                "directives":[
                    {{
                        "symbol": "TICKER",
                        "action": "BUY | SELL | HOLD | AVG DOWN | TAKE PARTIAL PROFIT | UPDATE TSL",
                        "reasoning": "A deep-dive explanation linking Global News + Sector Correlation + Technical Math.",
                        "the_why": "A robust, high-conviction paragraph explaining the specific catalyst and market structure."
                    }}
                ]
            }}
            Constraint: If technical data is missing, acknowledge the "Data Gap". Use professional terminology (Alpha, Beta, Mean Reversion, Liquidity Drain). Utilize the provided ATR-based TSL for math context.
            """

        # 📝 LOG THE EXACT PAYLOAD SENT
        self.logger.info(f"🚀 PAYLOAD SENT TO GEMINI:\n{prompt}")

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )

            raw_text = response.text.strip()

            # 📝 LOG THE RAW RESPONSE RECEIVED
            self.logger.info(f"📥 RAW JSON RECEIVED FROM GEMINI:\n{raw_text}")

            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].strip()

            parsed = json.loads(raw_text)
            if isinstance(parsed, str): parsed = json.loads(parsed)
            if not isinstance(parsed, dict): return self._fallback_response("Invalid structure.")

            return parsed

        except Exception as e:
            self.logger.error(f"JSON Parsing Error: {e}")
            return self._fallback_response("AI Output failed to parse.")

    def _fallback_response(self, reason: str):
        return {
            "market_vibe": reason,
            "macro_analysis": "Offline",
            "global_score": 0.0,
            "confidence_score": 0.0,
            "directives": []
        }
