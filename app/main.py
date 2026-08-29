from fastapi import FastAPI

from app.routes import account

app = FastAPI(
    title="EasyML API",
    version="1.0.0",
)

@app.get("/") 
async def root():
    return {"message": "Hello World!"}

app.include_router(account.router)