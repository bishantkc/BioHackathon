import uvicorn
from fastapi import FastAPI, Depends
from routers import traits, auth, appointments, roles, reports
from fastapi.middleware.cors import CORSMiddleware
from components import create_admin
from components.dependencies import get_db
from sqlalchemy.orm import Session


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(traits.router)
app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(roles.router)
app.include_router(reports.router)


@app.get("/")
async def root(db: Session = Depends(get_db)):
    await create_admin.create_admin_user(db)
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
