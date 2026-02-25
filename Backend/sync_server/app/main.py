from fastapi import FastAPI
from .database import engine, Base, SessionLocal
from .models import User, Task, TaskType
from .api import auth_routes, sync_routes

app = FastAPI(title="ProductivitySync Server")

app.include_router(auth_routes.router)
app.include_router(sync_routes.router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        count = session.query(TaskType).count()
        if count == 0:
            initial_types = [
                "Other", "Meeting", "Dust Cleaning", "Documentation",
                "Customer Support", "Code Bug Fix", "Research",
                "Optimization", "Deployment", "Project Management",
                "Feature Development"
            ]
            session.add_all([TaskType(name=t) for t in initial_types])
            session.commit()
            print("✅ Таблица task_types заполнена начальными данными")
        else:
            print("ℹ️ Таблица task_types уже заполнена")
    finally:
        session.close()

@app.get("/")
def read_root():
    return {"status": "online"}