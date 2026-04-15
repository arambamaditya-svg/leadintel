from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from db import engine
from models.database import Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LeadIntel", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routes
from routes.agency_routes import router as agency_router
from routes.lead_routes import router as lead_router

app.include_router(agency_router)
app.include_router(lead_router)

# Serve frontend files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def serve_index():
    index_path = os.path.join(frontend_path, "index.html")
    return FileResponse(index_path)

@app.get("/dashboard")
async def serve_dashboard():
    dashboard_path = os.path.join(frontend_path, "dashboard.html")
    return FileResponse(dashboard_path)

@app.get("/login")
async def serve_login():
    login_path = os.path.join(frontend_path, "login.html")
    return FileResponse(login_path)

@app.get("/register")
async def serve_register():
    register_path = os.path.join(frontend_path, "register.html")
    return FileResponse(register_path)

@app.get("/lead/{lead_id}")
async def serve_lead_detail(lead_id: int):
    lead_detail_path = os.path.join(frontend_path, "lead_detail.html")
    return FileResponse(lead_detail_path)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "LeadIntel API running"}

@app.get("/rules")
async def serve_rules():
    rules_path = os.path.join(frontend_path, "rules.html")
    return FileResponse(rules_path)