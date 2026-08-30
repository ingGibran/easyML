from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from typing import Optional

from app.security.current import get_current_account
from app.db.database import get_session
from app.db.models import Account, Dataset, DatasetCreate, DatasetRead
from app.storage.minio_service import upload_dataset, get_dataset_stream, update_dataset_file, delete_dataset_file

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

# Read All
@router.get("/read_all")
def read_all_datasets(
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):

    datasets = session.exec(
        select(Dataset).where(
            Dataset.AccountID == current_account.AccountID
        )
    ).all()
    
    return {"datasets": datasets}

# Read
@router.get("/{dataset_id}/download")
def download_dataset(
    dataset_id: int, 
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    
    dataset = session.exec( 
        select(Dataset).where(
            Dataset.DatasetID == dataset_id,
            Dataset.AccountID == current_account.AccountID
        )
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied")
    
    bucket_name = "dataset"
    
    try:
        file_stream = get_dataset_stream(bucket_name, dataset.File_Path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error retrieving file from storage: {str(e)}")
    
    media_type = "text/csv" if dataset.File_Format == "csv" else "application/json"
    headers = {
        "Content-Disposition": f"attachment; filename='{dataset.Name}.{dataset.File_Format}'"
    }
    
    def iterfile():
        try: 
            for chunk in file_stream.stream(32 * 1024):
                yield chunk
        finally: 
            file_stream.release_conn() 
    
    return StreamingResponse(iterfile(), media_type=media_type, headers=headers)


@router.put("/{dataset_id}")
def update_experiment(
    dataset_id: int, 
    Name: Optional[str] = Form(None, description="Dataset new name"),
    Description: Optional[str] = Form(None, description="Dataset new description"),
    file: Optional[UploadFile] = File(None, description="New File"),
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    
    dataset = session.exec( 
        select(Dataset).where(
            Dataset.DatasetID == dataset_id,
            Dataset.AccountID == current_account.AccountID
        )
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if file:
        filename = file.filename.lower()
        if not (filename.endswith(".csv") or filename.endswith(".json")):
            raise HTTPException(status_code=400, detail="Only CSV and JSON files are allowed")
        
        new_format = filename.split(".")[-1]
        content_type = "text/csv" if new_format == "csv" else "application/json"
        
        try:
            update_dataset_file(
                file_stream=file.file,
                file_size=file.size,
                bucket_name="dataset",
                object_name=Name,
                content_type=content_type 
            )
            dataset.File_Format = new_format
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating file in MinIO: {str(e)}")
        
        if Name and Name != dataset.Name:
            existing = session.exec(
                select(Dataset).where(
                    Dataset.AccountID == current_account.AccountID,
                    Dataset.Name == Name
                )
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail="A dataset with this new name alraedy exists")
            dataset.Name = Name 
        
        if Description is not None:
            dataset.Description = Description
        
        session.add(dataset)
        session.commit()
        session.refresh(dataset)
        
        return {"message": "Dataset updated successfully", "dataset_id": dataset.DatasetID}


@router.delete("/{dataset_id}")
def delete_experiment(
    dataset_id: int,
    current_account: Account = Depends(get_current_account),
    session: Session = Depends(get_session)
):
    
    dataset = session.exec(
        select(Dataset).where(
            Dataset.DatasetID == dataset_id,
            Dataset.AccountID == current_account.AccountID
        )
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied")
    
    try:
        delete_dataset_file(
            bucket_name="dataset",
            object_name=dataset.File_Path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file from storage: {str(e)}")
    
    session.delete(dataset)
    session.commit()
    
    return {"status": 200, "message": f"Dataset '{dataset.Name}' deleted successfully"}