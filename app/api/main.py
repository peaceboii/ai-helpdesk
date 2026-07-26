from fastapi import FastAPI
from app.api.routes import router
from app.services.database_service import init_db

app = FastAPI(title="AI Helpdesk Automation API", version="1.0.0")

# Initialize database tables on startup
init_db()

# Include routes
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "AI Helpdesk Automation Platform API is online."}
