import io

import pandas as pd
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

# pyrefly: ignore [missing-import]
from app.database.dependencies import get_db
# pyrefly: ignore [missing-import]
from app.database.models import SaleRecord
# pyrefly: ignore [missing-import]
from app.schemas.upload import (
    UploadErrorResponse,
    UploadResponse,
    ValidationError,
)

router = APIRouter(
    prefix="/upload",
    tags=["Upload"],
)

REQUIRED_COLUMNS = {
    "date",
    "product",
    "quantity_sold",
}

OPTIONAL_COLUMNS = {
    "sku",
    "category",
    "current_stock",
    "unit_cost",
    "reorder_point",
}

ALL_KNOWN_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS

COLUMN_ALIASES = {
    "product_name": "product",
    "product": "product",
    "units_sold": "quantity_sold",
    "qty_sold": "quantity_sold",
    "quantity": "quantity_sold",
    "stock": "current_stock",
    "current_stock": "current_stock",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    df = df.rename(
        columns={
            key: value
            for key, value in COLUMN_ALIASES.items()
            if key in df.columns
        }
    )

    return df


def validate_csv(df: pd.DataFrame):

    errors = []

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        errors.append(
            ValidationError(
                field="columns",
                message=f"Missing required columns: {', '.join(sorted(missing))}",
            )
        )
        return errors

    unknown = set(df.columns) - ALL_KNOWN_COLUMNS

    if unknown:
        errors.append(
            ValidationError(
                field="columns",
                message=f"Unknown columns ignored: {', '.join(sorted(unknown))}",
            )
        )

    for index, row in df.iterrows():

        row_number = index + 2

        try:
            pd.to_datetime(row["date"], errors="raise")
        except Exception:
            errors.append(
                ValidationError(
                    row=row_number,
                    field="date",
                    message=f"Invalid date: {row['date']}",
                )
            )

        if pd.isna(row["product"]) or str(row["product"]).strip() == "":
            errors.append(
                ValidationError(
                    row=row_number,
                    field="product",
                    message="Product cannot be empty",
                )
            )

        try:
            quantity = int(row["quantity_sold"])

            if quantity < 0:
                raise ValueError()

        except Exception:
            errors.append(
                ValidationError(
                    row=row_number,
                    field="quantity_sold",
                    message=f"Invalid quantity: {row['quantity_sold']}",
                )
            )

        if "current_stock" in df.columns:

            value = row.get("current_stock")

            if pd.notna(value):

                try:

                    stock = int(value)

                    if stock < 0:
                        raise ValueError()

                except Exception:

                    errors.append(
                        ValidationError(
                            row=row_number,
                            field="current_stock",
                            message=f"Invalid stock: {value}",
                        )
                    )

        if "reorder_point" in df.columns:

            value = row.get("reorder_point")

            if pd.notna(value):

                try:

                    reorder = int(value)

                    if reorder < 0:
                        raise ValueError()

                except Exception:

                    errors.append(
                        ValidationError(
                            row=row_number,
                            field="reorder_point",
                            message=f"Invalid reorder point: {value}",
                        )
                    )

        if "unit_cost" in df.columns:

            value = row.get("unit_cost")

            if pd.notna(value):

                try:

                    cost = float(value)

                    if cost < 0:
                        raise ValueError()

                except Exception:

                    errors.append(
                        ValidationError(
                            row=row_number,
                            field="unit_cost",
                            message=f"Invalid unit cost: {value}",
                        )
                    )

    return errors


def create_sale_record(row):

    return SaleRecord(

        sale_date=pd.to_datetime(
            row["date"]
        ).date(),

        product_name=str(
            row["product"]
        ).strip(),

        sku=(
            str(row["sku"]).strip()
            if pd.notna(row.get("sku"))
            else None
        ),

        category=(
            str(row["category"]).strip()
            if pd.notna(row.get("category"))
            else None
        ),

        quantity_sold=int(
            row["quantity_sold"]
        ),

        current_stock=(
            int(row["current_stock"])
            if pd.notna(row.get("current_stock"))
            else None
        ),

        unit_cost=(
            float(row["unit_cost"])
            if pd.notna(row.get("unit_cost"))
            else None
        ),

        reorder_point=(
            int(row["reorder_point"])
            if pd.notna(row.get("reorder_point"))
            else None
        ),
    )


@router.post(
    "",
    response_model=UploadResponse,
)
async def upload_sales_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if (
        not file.filename
        or not file.filename.lower().endswith(".csv")
    ):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    content = await file.read()

    try:

        dataframe = pd.read_csv(
            io.BytesIO(content)
        )

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=f"Could not parse CSV: {error}",
        )

    if dataframe.empty:

        raise HTTPException(
            status_code=400,
            detail="CSV file is empty.",
        )

    dataframe = normalize_columns(
        dataframe
    )

    errors = validate_csv(
        dataframe
    )

    critical_errors = [
        error
        for error in errors
        if error.field != "columns"
        or "Missing" in error.message
    ]

    if critical_errors:

        raise HTTPException(
            status_code=422,
            detail=UploadErrorResponse(
                message="CSV validation failed.",
                errors=critical_errors,
            ).model_dump(),
        )

    records = [
        create_sale_record(row)
        for _, row in dataframe.iterrows()
    ]

    # Clear cached model pkl files to force retraining from scratch on the new dataset
    from pathlib import Path
    model_dir = Path("app/ml/models")
    if model_dir.exists():
        for p in model_dir.glob("*.pkl"):
            try:
                p.unlink()
            except Exception:
                pass

    # Remove existing sales records for matching (sale_date, product_name) to avoid duplicates
    for rec in records:
        db.query(SaleRecord).filter(
            SaleRecord.sale_date == rec.sale_date,
            SaleRecord.product_name == rec.product_name
        ).delete()
    db.flush()

    db.bulk_save_objects(records)
    # Track upload history
    # pyrefly: ignore [missing-import]
    from app.database.models import UploadLog
    db.add(UploadLog(filename=file.filename))
    db.commit()

    dates = [
        record.sale_date
        for record in records
    ]

    products = {
        record.product_name
        for record in records
    }

    # Automatically generate predictions for all dates in dataset + next day
    try:
        # pyrefly: ignore [missing-import]
        from app.api.prediction import generate_predictions_for_all_dates
        generate_predictions_for_all_dates(db)
    except Exception as exc:
        print(f"[Upload] Auto-forecast error: {exc}")

    return UploadResponse(
        message="Sales data uploaded successfully.",
        rows_imported=len(records),
        products_found=len(products),
        date_range={
            "start": min(dates).isoformat(),
            "end": max(dates).isoformat(),
        },
    )


@router.get("/schema")
def csv_schema():

    return {
        "required_columns": sorted(
            REQUIRED_COLUMNS
        ),
        "optional_columns": sorted(
            OPTIONAL_COLUMNS
        ),
        "example_row": {
            "date": "2026-07-25",
            "product": "Organic Whole Milk",
            "quantity_sold": 25,
            "sku": "DAI-001",
            "category": "Dairy",
            "current_stock": 18,
            "unit_cost": 4.50,
            "reorder_point": 20,
        },
    }