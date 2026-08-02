import os
from datetime import date


class ExplanationEngine:

    @staticmethod
    def generate(
        predicted_demand: float,
        current_stock: int,
        confidence: float,
        history=None,
        date_val: date | None = None,
        product_name: str | None = None,
        category: str | None = None,
        reorder_point: int | None = None,
        model_type: str | None = None,
    ) -> str:
        target_date = date_val or date.today()
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        # 1. Try Gemini API if key is set
        if api_key:
            try:
                # pyrefly: ignore [missing-import]
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                
                avg_sales = history.tail(7).mean() if (history is not None and len(history) > 0) else 0.0
                prompt = (
                    f"You are RetailPilot AI, an expert retail demand forecasting assistant. "
                    f"Explain in 2 concise sentences why the AI model predicted a demand of {predicted_demand:.1f} units "
                    f"for '{product_name or 'Product'}' ({category or 'General'}) on {target_date.strftime('%B %d, %Y')}.\n"
                    f"Context Data:\n"
                    f"- Current Stock: {current_stock} units\n"
                    f"- Reorder Point: {reorder_point or 'N/A'}\n"
                    f"- 7-Day Sales Velocity Avg: {avg_sales:.1f} units/day\n"
                    f"- Model Confidence: {confidence:.1f}%\n"
                    f"- Forecasting Algorithm: {model_type or 'XGBoost'}\n"
                    f"Highlight recent momentum, inventory risk, and calendar/weekend drivers."
                )
                response = gemini_model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as err:
                print(f"[ExplanationEngine] Gemini API call skipped/fallback: {err}")

        # 2. Advanced Retail Analytics Engine Fallback
        reasons = []

        # Trend & Momentum Analysis
        if history is not None and len(history) > 0:
            recent_sales = history.tail(7)
            average_sales = float(recent_sales.mean())
            latest_sale = float(recent_sales.iloc[-1]) if len(recent_sales) else 0.0

            if latest_sale >= average_sales * 1.15:
                reasons.append(
                    f"Sales momentum is surging ({latest_sale:.0f} units sold vs 7-day avg of {average_sales:.1f})."
                )
            elif latest_sale <= average_sales * 0.85:
                reasons.append(
                    f"Sales velocity has slowed down slightly ({latest_sale:.0f} units sold vs 7-day avg of {average_sales:.1f})."
                )
            else:
                reasons.append(
                    f"Demand remains steady aligned with recent daily average ({average_sales:.1f} units/day)."
                )

        # Calendar & Day-of-Week Influencers
        weekday = target_date.weekday()
        if weekday in (4, 5, 6): # Fri, Sat, Sun
            reasons.append(
                "Weekend shopping traffic multiplier has been factored into the forecast."
            )
        else:
            reasons.append(
                "Standard weekday purchasing patterns apply."
            )

        # Holiday Season Adjustment
        m, d = target_date.month, target_date.day
        is_holiday = (
            (m == 12 and d >= 18) or (m == 1 and d <= 3) or
            (m == 7 and 1 <= d <= 6) or (m == 6 and d >= 28) or
            (m == 11 and 20 <= d <= 30) or (m == 9 and d <= 8)
        )
        if is_holiday:
            reasons.append(
                "Demand curve updated for upcoming holiday shopping volume."
            )

        # Stock & Buffer Health
        if current_stock == 0:
            reasons.append(
                "CRITICAL: Item is currently out of stock, causing immediate revenue risk."
            )
        elif current_stock < predicted_demand:
            deficit = int(predicted_demand - current_stock)
            reasons.append(
                f"Inventory shortfall detected: stock ({current_stock}) is below expected demand by ~{deficit} units."
            )
        else:
            surplus = int(current_stock - predicted_demand)
            reasons.append(
                f"Inventory buffer is healthy with ~{surplus} excess units post-forecast."
            )

        # Statistical Model Performance
        if confidence >= 90:
            reasons.append(
                f"High model statistical confidence ({confidence:.1f}%) based on low variance history."
            )
        elif confidence >= 75:
            reasons.append(
                f"Moderate confidence ({confidence:.1f}%) with standard baseline error bounds."
            )
        else:
            reasons.append(
                f"Confidence is {confidence:.1f}% due to limited historical training records."
            )

        return " ".join(reasons)