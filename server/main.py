import uvicorn
from fastapi import FastAPI, Depends
from routers import traits

app = FastAPI()

app.include_router(traits.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
