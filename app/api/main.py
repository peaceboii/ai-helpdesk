from fastapi import FastAPI
from app.api.routes import router
from app.services.database_service import init_db
from app.services.listener_service import ListenerServiceManager

app = FastAPI(title="AI Helpdesk Automation API", version="1.0.0")

# Initialize database tables on startup
init_db()

# Include routes
app.include_router(router)

# Initialize and run integration listeners
listener_manager = ListenerServiceManager()

@app.on_event("startup")
def startup_event():
    listener_manager.start()

@app.on_event("shutdown")
def shutdown_event():
    listener_manager.stop()

@app.get("/")
def read_root():
    return {"message": "AI Helpdesk Automation Platform API is online."}
