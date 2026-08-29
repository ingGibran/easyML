from fastapi import FastAPI

app = FastAPI(
    title="EasyML API"
)

@app.get("/") 
async def root():
    return {"message": "Hello World!"}