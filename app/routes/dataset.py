from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select
from typing import Optional

from app.security.current import get_current_account
from app.db.database import get_session
from app.db.models import Account, Dataset, DatasetCreate, DatasetRead
from app.storage.minio_service import upload_dataset

router = APIRouter(
    prefix="/dataset",
    tags=["Dataset"]
)


# Upload
@router.post("/upload")
def create_experiment(
    Name: str,
    Description: Optional[str],
    file: UploadFile = File(...),
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):

    # Verify filename
    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".json")):
        raise HTTPException(status_code=400, detail="Only CSV and JSON files are allowed")
    
    dataset_format = filename.split(".")[-1]
    
    existing_filename = session.exec(
        select(Dataset).where(
            Dataset.AccountID == current_account.AccountID,
            Dataset.Name == Name
        )
    ).first()
    
    if existing_filename:
        raise HTTPException(status_code=409, detail="Repeated dataset name")
    
    bucket_name = "dataset"
    try:
        file_size = file.size 
        
        object_path = upload_dataset(
            file_stream=file.file,
            file_size=file_size,
            bucket_name=bucket_name,
            account_id=current_account.AccountID,
            dataset_name=Name,
            dataset_format=dataset_format
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    dataset_new = Dataset(
        Name=Name,
        Description=Description,
        File_Path=object_path,
        File_Format=dataset_format,
        AccountID=current_account.AccountID
    )
    
    session.add(dataset_new) 
    session.commit()
    session.refresh(dataset_new)
    
    return {"message": "Dataset uploaded successfully", "dataset_id": dataset_new.DatasetID, "dataset_path": object_path} 