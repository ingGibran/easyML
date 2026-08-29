from minio import Minio 

client = Minio( 
    endpoint=...,
    access_key=...,
    secret_key=...,
    secure=False
)