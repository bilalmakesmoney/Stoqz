import math

STOCK_COVERAGE_DAYS = 2.5  # 2.5 days target stock buffer for retail replenishment

def calculate_order(
    predicted_demand: float,
    current_stock: int,
    reorder_point: int | None = None,
) -> int:
    """
    Calculate optimal reorder quantity based on 2.5 days of predicted demand
    and current inventory levels.
    """
    daily_demand = max(0.0, float(predicted_demand))
    
    # Target stock level (2.5 days of predicted demand)
    target_stock = math.ceil(daily_demand * STOCK_COVERAGE_DAYS)
    
    if reorder_point is not None and reorder_point > 0:
        target_stock = max(target_stock, math.ceil(reorder_point * 1.5))

    # Calculate required order quantity to reach target stock
    needed = target_stock - current_stock
    if needed > 0:
        return max(5, math.ceil(needed))
    
    return 0