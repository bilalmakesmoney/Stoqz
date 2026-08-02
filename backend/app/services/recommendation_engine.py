class RecommendationEngine:

    @staticmethod
    def generate():
        return [
            {
                "title": "Increase stock for fast-selling products",
                "priority": "High",
            },
            {
                "title": "Run discounts on slow-moving inventory",
                "priority": "Medium",
            },
            {
                "title": "Check products below reorder point",
                "priority": "High",
            },
            {
                "title": "Review supplier lead times",
                "priority": "Low",
            },
        ]