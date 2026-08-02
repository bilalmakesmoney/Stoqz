class RiskEngine:

    @staticmethod
    def analyze(
        predicted_demand: float,
        current_stock: int,
    ):

        difference = current_stock - predicted_demand

        if current_stock == 0:
            return {
                "risk": "OUT_OF_STOCK",
                "message": "No inventory available.",
                "severity": "critical",
            }

        if difference < 0:
            return {
                "risk": "STOCKOUT",
                "message": f"Inventory may fall short by {abs(round(difference))} units.",
                "severity": "high",
            }

        if difference <= predicted_demand * 0.2:
            return {
                "risk": "LOW_STOCK",
                "message": "Stock is sufficient but running low.",
                "severity": "medium",
            }

        if difference >= predicted_demand:
            return {
                "risk": "OVERSTOCK",
                "message": f"Approximately {round(difference)} units may remain unsold.",
                "severity": "low",
            }

        return {
            "risk": "HEALTHY",
            "message": "Inventory level looks healthy.",
            "severity": "none",
        }