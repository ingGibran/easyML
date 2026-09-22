from enum import Enum

import polars as pl
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import Account, Dataset
from app.security.current import get_current_account
from app.storage.minio_service import get_dataset_stream, save_dataset

router = APIRouter(
    prefix="/data",
    tags=["Data"]
)


# ============================================================
# Types
# ============================================================

class ColumnType(str, Enum):
    INT8 = "Int8"
    INT16 = "Int16"
    INT32 = "Int32"
    INT64 = "Int64"

    FLOAT32 = "Float32"
    FLOAT64 = "Float64"

    STRING = "String"
    BOOLEAN = "Boolean"

    DATE = "Date"
    DATETIME = "Datetime"


POLARS_TYPES = {
    ColumnType.INT8: pl.Int8,
    ColumnType.INT16: pl.Int16,
    ColumnType.INT32: pl.Int32,
    ColumnType.INT64: pl.Int64,

    ColumnType.FLOAT32: pl.Float32,
    ColumnType.FLOAT64: pl.Float64,

    ColumnType.STRING: pl.String,
    ColumnType.BOOLEAN: pl.Boolean,

    ColumnType.DATE: pl.Date,
    ColumnType.DATETIME: pl.Datetime,
}


class CastColumnRequest(BaseModel):
    column_name: str
    column_type: ColumnType


class DatasetPreview(BaseModel):
    columns: list[str]
    rows: list[dict]
    returned_rows: int


# ============================================================
# Temporary editing state
# ============================================================

# PROVISIONAL:
# This should eventually be replaced by persistent storage
# or a proper editing session.
dataset_actions: dict[int, list[dict]] = {}


# ============================================================
# Helpers
# ============================================================

def get_dataset_or_404(
    dataset_id: int,
    current_user: Account,
    session: Session
) -> Dataset:

    dataset = session.exec(
        select(Dataset).where(
            Dataset.DatasetID == dataset_id,
            Dataset.AccountID == current_user.AccountID
        )
    ).first()

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found or access denied"
        )

    return dataset


def load_dataset(
    dataset: Dataset,
    limit: int | None = None
) -> pl.DataFrame:

    bucket_name = "dataset"

    try:
        file_stream = get_dataset_stream(
            bucket_name,
            dataset.File_Path
        )

        try:
            if dataset.File_Format == "csv":

                if limit is not None:
                    return pl.read_csv(
                        file_stream,
                        n_rows=limit
                    )

                return pl.read_csv(file_stream)

            elif dataset.File_Format == "json":

                df = pl.read_json(file_stream)

                if limit is not None:
                    return df.head(limit)

                return df

            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported format: {dataset.File_Format}"
                )

        finally:
            file_stream.close()
            file_stream.release_conn()

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading dataset: {str(e)}"
        )


def apply_actions(
    df: pl.DataFrame,
    actions: list[dict]
) -> pl.DataFrame:

    for action in actions:

        action_name = action["action"]

        # --------------------------------------------
        # Remove column
        # --------------------------------------------

        if action_name == "remove":

            column_name = action["column_name"]

            if column_name not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Column '{column_name}' does not exist "
                        "in the current dataset state"
                    )
                )

            df = df.drop(column_name)

        # --------------------------------------------
        # Cast column
        # --------------------------------------------

        elif action_name == "cast":

            column_name = action["column_name"]
            column_type = action["column_type"]

            if column_name not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Column '{column_name}' does not exist "
                        "in the current dataset state"
                    )
                )

            dtype = POLARS_TYPES[column_type]

            try:
                df = df.with_columns(
                    pl.col(column_name).cast(
                        dtype,
                        strict=False
                    )
                )

            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Could not cast column '{column_name}' "
                        f"to {column_type}: {str(e)}"
                    )
                )

        else:

            raise HTTPException(
                status_code=400,
                detail=f"Unknown action: {action_name}"
            )

    return df


# ============================================================
# Actions
# ============================================================

@router.post("/remove_column")
def remove_column(
    dataset_id: int,
    column_name: str,
    current_user: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    dataset = get_dataset_or_404(
        dataset_id,
        current_user,
        session
    )

    # Load only enough data to know the current schema.
    df = load_dataset(dataset, limit=1)

    if column_name not in df.columns:
        raise HTTPException(
            status_code=404,
            detail=f"Column '{column_name}' not found"
        )

    actions = dataset_actions.setdefault(dataset_id, [])

    action = {
        "action": "remove",
        "column_name": column_name
    }

    actions.append(action)

    return {
        "status": "Column removal added",
        "action": action
    }


@router.post("/cast_column")
def cast_column(
    dataset_id: int,
    column_info: CastColumnRequest,
    current_user: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    dataset = get_dataset_or_404(
        dataset_id,
        current_user,
        session
    )

    # Load only enough data to know the current schema.
    df = load_dataset(dataset, limit=1)

    if column_info.column_name not in df.columns:
        raise HTTPException(
            status_code=404,
            detail=f"Column '{column_info.column_name}' not found"
        )

    actions = dataset_actions.setdefault(dataset_id, [])

    action = {
        "action": "cast",
        "column_name": column_info.column_name,
        "column_type": column_info.column_type
    }

    actions.append(action)

    return {
        "status": "Column cast added",
        "action": action
    }


# ============================================================
# Preview
# ============================================================

@router.get(
    "/dataset/preview",
    response_model=DatasetPreview
)
def get_dataset_preview(
    dataset_id: int,
    limit: int = 10,
    current_user: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):

    # --------------------------------------------
    # Validate limit
    # --------------------------------------------

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100"
        )

    # --------------------------------------------
    # Get dataset
    # --------------------------------------------

    dataset = get_dataset_or_404(
        dataset_id,
        current_user,
        session
    )

    # --------------------------------------------
    # Load original dataset
    # --------------------------------------------

    df = load_dataset(
        dataset,
        limit=limit
    )

    # --------------------------------------------
    # Get pending actions
    # --------------------------------------------

    actions = dataset_actions.get(
        dataset_id,
        []
    )

    # --------------------------------------------
    # Apply transformations
    # --------------------------------------------

    df = apply_actions(
        df,
        actions
    )

    # --------------------------------------------
    # Return preview
    # --------------------------------------------

    return DatasetPreview(
        columns=df.columns,
        rows=df.to_dicts(),
        returned_rows=df.height
    )


# ============================================================
# Get pending actions
# ============================================================

@router.get("/actions")
def get_actions(
    dataset_id: int,
    current_user: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):

    # Validate ownership/access
    get_dataset_or_404(
        dataset_id,
        current_user,
        session
    )

    return {
        "dataset_id": dataset_id,
        "actions": dataset_actions.get(
            dataset_id,
            []
        )
    }


# ============================================================
# Reset actions
# ============================================================

@router.delete("/actions")
def reset_actions(
    dataset_id: int,
    current_user: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):

    get_dataset_or_404(
        dataset_id,
        current_user,
        session
    )

    dataset_actions.pop(
        dataset_id,
        None
    )

    return {
        "status": "Actions reset successfully"
    }


# ============================================================
# Save Actions
# ============================================================

@router.post("/dataset/save")
def save_dataset_changes(
    dataset_id: int,
    current_user: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    # ------------------------------------------------
    # Get dataset and verify ownership
    # ------------------------------------------------

    dataset = get_dataset_or_404(
        dataset_id,
        current_user,
        session
    )

    # ------------------------------------------------
    # Get pending actions
    # ------------------------------------------------

    actions = dataset_actions.get(
        dataset_id,
        []
    )

    if not actions:
        return {
            "status": "No changes to save",
            "dataset_id": dataset_id
        }

    # ------------------------------------------------
    # Load complete original dataset
    # ------------------------------------------------

    df = load_dataset(dataset)

    # ------------------------------------------------
    # Apply pending transformations
    # ------------------------------------------------

    df = apply_actions(
        df,
        actions
    )

    # ------------------------------------------------
    # Save modified dataset to MinIO
    # ------------------------------------------------

    try:
        save_dataset(
            bucket_name="dataset",
            object_name=dataset.File_Path,
            df=df,
            file_format=dataset.File_Format
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving dataset: {str(e)}"
        )

    # ------------------------------------------------
    # Remove pending actions
    # ------------------------------------------------

    dataset_actions.pop(
        dataset_id,
        None
    )

    return {
        "status": "Dataset updated successfully",
        "dataset_id": dataset_id,
        "columns": df.columns,
        "rows": df.height
    }