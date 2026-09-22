import os
from minio import Minio
from minio.error import S3Error
from io import BytesIO
import polars as pl

from app.core.config import settings

client = Minio(
    "minio:9000",
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=False
)

# Upload New
def upload_dataset(file_stream, file_size: int, bucket_name: str, account_id: int, dataset_name: str, dataset_format:str):
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Bucket {bucket_name} was created")
        else:
            print(f"Bucket {bucket_name} exists already")
        
        object_name = f"{account_id}/{dataset_name}.{dataset_format}"
        content_type = "text/csv" if dataset_format == "csv" else "application/json"
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file_stream,
            length=file_size,
            content_type=content_type
        )
        
        print("File saved successfully")
        return object_name
        
    except S3Error as exc:
        print("Upload failed:", exc)
        raise exc

# Read
def get_dataset_stream(bucket_name: str, object_name: str):
    try:
        response = client.get_object(bucket_name, object_name)
        return response 
    except S3Error as exc:
        print(f"Error reading file {object_name}: ", exc)
        raise exc

# Upload All
def update_dataset_file(file_stream, file_size: int, bucket_name: str, object_name: str, content_type: str):
    try:
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=file_stream,
            length=file_size,
            content_type=content_type
        )
        print(f"File {object_name} overwritten succesfully")
    except S3Error as exc:
        print("Overwrite failed:", exc)
        raise exc

# Upload Actions
def save_dataset(
    bucket_name: str,
    object_name: str,
    df: pl.DataFrame,
    file_format: str
):
    buffer = BytesIO()

    if file_format == "csv":
        df.write_csv(buffer)
        content_type = "text/csv"

    elif file_format == "json":
        df.write_json(buffer)
        content_type = "application/json"

    else:
        raise ValueError(
            f"Unsupported dataset format: {file_format}"
        )

    buffer.seek(0)

    data = buffer.getbuffer()

    client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=buffer,
        length=len(data),
        content_type=content_type
    )

# Remove
def delete_dataset_file(bucket_name: str, object_name:str):

    try:
        client.remove_object(bucket_name, object_name)
        print(f"File {object_name} deleted successfully form minIO")
    except S3Error as exc:
        print("Deleted failed:", exc)
        raise exc
