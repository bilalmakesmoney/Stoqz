# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import func

# pyrefly: ignore [missing-import]
from app.database.database import get_db
# pyrefly: ignore [missing-import]
from app.database.models import PredictionRecord

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    predictions = db.query(PredictionRecord).all()

    if not predictions:
        return {
            "total_products": 0,
            "total_order_units": 0,
            "high_risk_products": 0,
            "average_confidence": 0,
        }

    total_products = len(predictions)

    total_order_units = sum(
        p.recommended_order for p in predictions
    )

    high_risk = len(
        [
            p
            for p in predictions
            if getattr(p, "severity", "") == "High"
        ]
    )

    avg_confidence = round(
        sum(p.confidence for p in predictions) / total_products,
        2,
    )

    return {
        "total_products": total_products,
        "total_order_units": total_order_units,
        "high_risk_products": high_risk,
        "average_confidence": avg_confidence,
    }


@router.get("/alerts")
def alerts(db: Session = Depends(get_db)):

    predictions = (
        db.query(PredictionRecord)
        .order_by(PredictionRecord.recommended_order.desc())
        .all()
    )

    alerts = []

    for p in predictions:

        if p.recommended_order > 50:

            alerts.append(
                {
                    "product": p.product_name,
                    "message": f"Urgent reorder required ({p.recommended_order} units)",
                }
            )

    return alerts


@router.get("/top-products")
def top_products(db: Session = Depends(get_db)):

    products = (
        db.query(PredictionRecord)
        .order_by(PredictionRecord.predicted_demand.desc())
        .limit(5)
        .all()
    )

    return [
        {
            "product": p.product_name,
            "predicted_demand": p.predicted_demand,
            "recommended_order": p.recommended_order,
            "confidence": p.confidence,
        }
        for p in products
    ]


@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    from datetime import date, timedelta
    # pyrefly: ignore [missing-import]
    from app.database.models import SaleRecord, Product, PredictionRecord
    
    # 1. Today (max date in SaleRecord)
    max_date = db.query(func.max(SaleRecord.sale_date)).scalar()
    if max_date is None:
        from datetime import date
        today = date.today()
        return {
            "is_empty": True,
            "today_date": today.strftime("%A, %b %d"),
            "kpi": {
                "revenue": {"value": "₹0", "change": "0%"},
                "stock": {"value": "0", "change": "0%"},
                "reorder": {"value": "0", "change": "0%"},
                "accuracy": {"value": "0.0%", "change": "0%"}
            },
            "sales_trend": [],
            "inventory_status": [],
            "reorder_items": [],
            "recent_predictions": []
        }
    else:
        # max_date could be a string or date object depending on SQLite engine
        if isinstance(max_date, str):
            today = date.fromisoformat(max_date)
        else:
            today = max_date
            
    yesterday = today - timedelta(days=1)
    
    # 2. Get sales for today and yesterday (grouped by product_name to deduplicate double uploads)
    sales_today = db.query(
        SaleRecord.product_name,
        SaleRecord.sku,
        SaleRecord.category,
        func.max(SaleRecord.quantity_sold).label("quantity_sold"),
        func.max(SaleRecord.current_stock).label("current_stock"),
        func.max(SaleRecord.unit_cost).label("unit_cost"),
        func.max(SaleRecord.reorder_point).label("reorder_point")
    ).filter(SaleRecord.sale_date == today).group_by(SaleRecord.product_name).all()
    
    sales_yesterday = db.query(
        SaleRecord.product_name,
        SaleRecord.sku,
        SaleRecord.category,
        func.max(SaleRecord.quantity_sold).label("quantity_sold"),
        func.max(SaleRecord.current_stock).label("current_stock"),
        func.max(SaleRecord.unit_cost).label("unit_cost"),
        func.max(SaleRecord.reorder_point).label("reorder_point")
    ).filter(SaleRecord.sale_date == yesterday).group_by(SaleRecord.product_name).all()
    
    # 3. Product price mapping
    products = {p.name: p.unit_price for p in db.query(Product).all()}
    
    def get_revenue(sales):
        rev = 0.0
        for s in sales:
            price = products.get(s.product_name)
            if price is None:
                price = (s.unit_cost or 0.0) * 1.5
            rev += s.quantity_sold * price
        return round(rev, 2)
        
    rev_today = get_revenue(sales_today)
    rev_yesterday = get_revenue(sales_yesterday)
    
    rev_change = 0.0
    if rev_yesterday > 0:
        rev_change = round(((rev_today - rev_yesterday) / rev_yesterday) * 100, 1)
        
    # Stock totals
    stock_today = sum(s.current_stock for s in sales_today if s.current_stock is not None)
    stock_yesterday = sum(s.current_stock for s in sales_yesterday if s.current_stock is not None)
    
    stock_change = 0.0
    if stock_yesterday > 0:
        stock_change = round(((stock_today - stock_yesterday) / stock_yesterday) * 100, 1)
        
    # Reorders
    reorder_today = sum(1 for s in sales_today if s.current_stock is not None and s.reorder_point is not None and s.current_stock <= s.reorder_point)
    reorder_yesterday = sum(1 for s in sales_yesterday if s.current_stock is not None and s.reorder_point is not None and s.current_stock <= s.reorder_point)
    
    reorder_change = 0.0
    if reorder_yesterday > 0:
        reorder_change = round(((reorder_today - reorder_yesterday) / reorder_yesterday) * 100, 1)

    # Accuracy calculation based on latest predictions
    def get_prediction_accuracy(target_date):
        preds = db.query(PredictionRecord).filter(PredictionRecord.prediction_date == target_date).order_by(PredictionRecord.created_at.desc()).all()
        if not preds:
            recent_date = db.query(func.max(PredictionRecord.prediction_date)).filter(PredictionRecord.prediction_date <= target_date).scalar()
            if recent_date:
                preds = db.query(PredictionRecord).filter(PredictionRecord.prediction_date == recent_date).order_by(PredictionRecord.created_at.desc()).all()
            else:
                return 0.0
        unique_preds = []
        seen = set()
        for p in preds:
            if p.product_name not in seen:
                seen.add(p.product_name)
                unique_preds.append(p)

        errors = []
        for p in unique_preds:
            sale = db.query(
                SaleRecord.product_name,
                func.max(SaleRecord.quantity_sold).label("quantity_sold")
            ).filter(
                SaleRecord.product_name == p.product_name,
                SaleRecord.sale_date == target_date
            ).group_by(SaleRecord.product_name).first()

            if sale and sale.quantity_sold > 0:
                err = abs(p.predicted_demand - sale.quantity_sold) / sale.quantity_sold
                errors.append(err)
        if not errors:
            return 0.0
        avg_err = sum(errors) / len(errors)
        return max(0.0, round((1.0 - avg_err) * 100, 1))

    accuracy_today = get_prediction_accuracy(today)
    accuracy_yesterday = get_prediction_accuracy(yesterday)
    accuracy_change = round(accuracy_today - accuracy_yesterday, 1)

    # 5. Sales trend (past 7 days)
    sales_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_sales = db.query(SaleRecord).filter(SaleRecord.sale_date == day).all()
        day_rev = get_revenue(day_sales)
        day_name = day.strftime("%a")
            
        sales_trend.append({
            "name": day_name,
            "revenue": day_rev
        })
        
    # 6. Inventory Status by Category
    categories = ["Beverages", "Snacks", "Dairy", "Produce", "Household", "Personal Care"]
    inventory_status = []
    for cat in categories:
        cat_sales = [s for s in sales_today if s.category == cat]
        if not cat_sales:
            # No sales data for this category; set inventory metrics to zero
            inventory_status.append({
                "category": cat,
                "in_stock": 0,
                "low": 0,
                "out": 0,
                "total": 0,
            })
            continue
            
        total_products = len(cat_sales)
        in_stock_cnt = sum(1 for s in cat_sales if s.current_stock is not None and s.reorder_point is not None and s.current_stock > s.reorder_point)
        low_cnt = sum(1 for s in cat_sales if s.current_stock is not None and s.reorder_point is not None and 0 < s.current_stock <= s.reorder_point)
        out_cnt = sum(1 for s in cat_sales if s.current_stock == 0)
        
        # total items in stock sum
        total_items = sum(s.current_stock for s in cat_sales if s.current_stock is not None)
        
        # Wait, the label shows "100 items", "82 items" etc.
        # Let's map total items to screenshot values if default date to match exactly
        inventory_status.append({
            "category": cat,
            "in_stock": round(in_stock_cnt / total_products * 100) if total_products > 0 else 0,
            "low": round(low_cnt / total_products * 100) if total_products > 0 else 0,
            "out": round(out_cnt / total_products * 100) if total_products > 0 else 0,
            "total": total_items
        })
        
    # 7. Products Needing Reorder
    reorder_items = []
    # Query tomorrow's predictions for suggested orders
    tomorrow = today + timedelta(days=1)
    preds = db.query(PredictionRecord).filter(PredictionRecord.prediction_date == tomorrow).all()
    pred_map = {p.product_name: p.recommended_order for p in preds}
    
    for s in sales_today:
        suggested = pred_map.get(s.product_name, 0)
        rp = s.reorder_point or 15
        if s.current_stock is not None and (s.current_stock <= rp * 1.5 or suggested > 0):
            if suggested == 0:
                suggested = max(10, int(rp * 1.5 - s.current_stock))
            
            reorder_items.append({
                "product_name": s.product_name,
                "sku": s.sku,
                "category": s.category,
                "current_stock": s.current_stock,
                "reorder_point": rp,
                "suggested": f"+{suggested}",
                "status": "Out of Stock" if s.current_stock == 0 else "Low Stock" if s.current_stock <= rp else "Stock Replenishment"
            })
            
    reorder_items.sort(key=lambda x: (x["current_stock"] > 0, x["product_name"]))
    
    # 8. Recent Predictions Comparison
    recent_predictions = []
    # Query predictions for dates up to today (where actual sales are evaluated)
    recent_preds = db.query(PredictionRecord).filter(PredictionRecord.prediction_date <= today).order_by(PredictionRecord.prediction_date.desc(), PredictionRecord.created_at.desc()).all()
    
    # Deduplicate predictions by product_name to keep only the latest forecast per product
    unique_preds = []
    seen_preds = set()
    for p in recent_preds:
        if p.product_name not in seen_preds:
            seen_preds.add(p.product_name)
            unique_preds.append(p)
    recent_preds = unique_preds
    
    # Check number of CSV uploads performed
    # pyrefly: ignore [missing-import]
    from app.database.models import UploadLog
    upload_count = db.query(UploadLog).count()
    if upload_count == 0:
        unique_dates_count = db.query(func.count(func.distinct(SaleRecord.sale_date))).scalar() or 0
        is_multi_upload = unique_dates_count > 7
    else:
        is_multi_upload = upload_count >= 2

    actual_sales_map = {}
    for sale in db.query(SaleRecord).all():
        actual_sales_map[(sale.product_name, sale.sale_date)] = sale.quantity_sold
        
    for p in recent_preds:
        if is_multi_upload:
            actual = actual_sales_map.get((p.product_name, p.prediction_date))
            if actual is not None:
                pct_error = abs(p.predicted_demand - actual) / actual if actual > 0 else 0
                if pct_error <= 0.15:
                    status = "Accurate"
                elif p.predicted_demand < actual:
                    status = "Under"
                else:
                    status = "Over"
                actual_val = str(actual)
            else:
                status = "Pending"
                actual_val = "-"
        else:
            status = "Pending"
            actual_val = "-"
            
        recent_predictions.append({
            "product_name": p.product_name,
            "sku": p.sku,
            "category": p.category,
            "date": p.prediction_date.strftime("%b %d"),
            "predicted": round(p.predicted_demand),
            "actual": actual_val,
            "confidence": round(p.confidence),
            "status": status,
            "suggested": f"+{p.recommended_order}",
            "explanation": p.explanation or ""
        })
            
    recent_predictions.sort(key=lambda x: (x["date"], x["product_name"]), reverse=True)
    recent_predictions = recent_predictions[:15]
    
    # 9. Dynamic recommendations
    recommendations_list = []
    for s in sales_today:
        suggested = pred_map.get(s.product_name, 0)
        if s.current_stock == 0:
            if suggested == 0:
                suggested = max(10, int((s.reorder_point or 8) * 1.5))
            recommendations_list.append({
                "priority": "HIGH PRIORITY",
                "title": f"Reorder Urgent Out of Stock: {s.product_name}",
                "description": f"{s.product_name} is currently out of stock. Reordering {suggested} units immediately is suggested to avoid stockout costs.",
                "action_text": "Place Urgent Order"
            })
        elif s.reorder_point is not None and s.current_stock <= s.reorder_point:
            if suggested == 0:
                suggested = max(10, int(s.reorder_point * 1.5 - s.current_stock))
            recommendations_list.append({
                "priority": "MEDIUM PRIORITY",
                "title": f"Refill Low Stock: {s.product_name}",
                "description": f"{s.product_name} stock level ({s.current_stock}) is below reorder threshold ({s.reorder_point}). Recommended order of {suggested} units.",
                "action_text": "Refill Stock"
            })
            
    # Add a slow moving item suggestion if any
    slow_moving = [s for s in sales_today if s.current_stock is not None and s.reorder_point is not None and s.current_stock > s.reorder_point * 2]
    if slow_moving:
        s = slow_moving[0]
        recommendations_list.append({
            "priority": "LOW PRIORITY",
            "title": f"Promote Slow-Moving: {s.product_name}",
            "description": f"{s.product_name} has high stock levels ({s.current_stock} units) relative to sales velocity. Suggest launching POS discounts.",
            "action_text": "Activate Promotion"
        })
        
    # Sort: HIGH first, then MEDIUM, then LOW
    def rec_sort_key(x):
        if x["priority"].startswith("HIGH"):
            return 0
        if x["priority"].startswith("MEDIUM"):
            return 1
        return 2
        
    recommendations_list.sort(key=rec_sort_key)
    recommendations_list = recommendations_list[:9]
    
    accuracy_kpi = (
        {"value": f"{accuracy_today:.1f}%", "change": f"{'+' if accuracy_change >= 0 else ''}{accuracy_change}%"}
        if is_multi_upload
        else {"value": "-", "change": "-"}
    )
    
    return {
        "today_date": today.strftime("%A, %b %d"),
        "kpi": {
            "revenue": {"value": f"₹{rev_today:,.0f}", "change": f"{'+' if rev_change >= 0 else ''}{rev_change}%"},
            "stock": {"value": f"{stock_today:,}", "change": f"{'+' if stock_change >= 0 else ''}{stock_change}%"},
            "reorder": {"value": str(reorder_today), "change": f"{'+' if reorder_change >= 0 else ''}{reorder_change}%"},
            "accuracy": accuracy_kpi
        },
        "sales_trend": sales_trend,
        "inventory_status": inventory_status,
        "reorder_items": reorder_items,
        "recent_predictions": recent_predictions,
        "recommendations": recommendations_list
    }


@router.post("/restock")
def restock_product(product_name: str, quantity: int, db: Session = Depends(get_db)):
    # pyrefly: ignore [missing-import]
    from app.database.models import SaleRecord
    
    max_date = db.query(func.max(SaleRecord.sale_date)).scalar()
    if not max_date:
        return {"success": False, "message": "No sales records found."}
        
    records = db.query(SaleRecord).filter(
        SaleRecord.product_name == product_name,
        SaleRecord.sale_date == max_date
    ).all()
    
    if not records:
        return {"success": False, "message": f"Product '{product_name}' not found."}
        
    for r in records:
        current = r.current_stock or 0
        r.current_stock = current + quantity
        
    db.commit()
    return {"success": True, "message": f"Added {quantity} units to {product_name}."}