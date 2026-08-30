from fastapi import FastAPI

from app.routes import account, project, dataset

app = FastAPI(
    title="EasyML API",
    version="1.0.0",
)

@app.get("/") 
async def root():
    return {"message": "Hello World!"}

app.include_router(account.router)
app.include_router(project.router)
app.include_router(dataset.router)