


"""
# Sort
@router.get("/sample/{dataset_id}")
def sample_dataset(
    
    dataset_id: int,
    rows_number: int,
    column_name: str,
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

    
    df = pl.read_csv(file_stream.data) if dataset.File_Format == "csv" else pl.read_json(file_stream.data)

    if column_name not in df.columns:
        raise HTTPException(status_code=409, detail="Wrong column name")
    
    df = df.sort(column_name)
    
    return df.head(rows_number).to_dicts()
"""