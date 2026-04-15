import sys
print("DEBUG: Step 1 - app.py started", file=sys.stderr)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

print("DEBUG: Step 2 - imports done", file=sys.stderr)

from db import engine
from models.database import Base

print("DEBUG: Step 3 - db and models imported", file=sys.stderr)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    print("DEBUG: Step 4 - tables created successfully", file=sys.stderr)
except Exception as e:
    print(f"DEBUG: Step 4 FAILED - {e}", file=sys.stderr)
    raise

app = FastAPI(title="LeadIntel", version="0.1.0")

print("DEBUG: Step 5 - FastAPI app created", file=sys.stderr)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("DEBUG: Step 6 - CORS middleware added", file=sys.stderr)

# Import and include routes
try:
    from routes.agency_routes import router as agency_router
    print("DEBUG: Step 7 - agency_routes imported", file=sys.stderr)
except Exception as e:
    print(f"DEBUG: Step 7 FAILED - {e}", file=sys.stderr)
    raise

try:
    from routes.lead_routes import router as lead_router
    print("DEBUG: Step 8 - lead_routes imported", file=sys.stderr)
except Exception as e:
    print(f"DEBUG: Step 8 FAILED - {e}", file=sys.stderr)
    raise

try:
    from routes.webhook_routes import router as webhook_router
    print("DEBUG: Step 8.5 - webhook_routes imported", file=sys.stderr)
except Exception as e:
    print(f"DEBUG: Step 8.5 FAILED - {e}", file=sys.stderr)
    raise

app.include_router(agency_router)
app.include_router(lead_router)
app.include_router(webhook_router)

print("DEBUG: Step 9 - routes included", file=sys.stderr)

# Serve frontend files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
print(f"DEBUG: Step 10 - frontend path: {frontend_path}", file=sys.stderr)

# Check if frontend folder exists
if os.path.exists(frontend_path):
    print("DEBUG: Step 11 - frontend folder exists", file=sys.stderr)
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
else:
    print("DEBUG: Step 11 - frontend folder NOT FOUND", file=sys.stderr)

@app.get("/")
async def serve_index():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"error": "index.html not found"}

@app.get("/dashboard")
async def serve_dashboard():
    dashboard_path = os.path.join(frontend_path, "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        return {"error": "dashboard.html not found"}

@app.get("/login")
async def serve_login():
    login_path = os.path.join(frontend_path, "login.html")
    if os.path.exists(login_path):
        return FileResponse(login_path)
    else:
        return {"error": "login.html not found"}

@app.get("/register")
async def serve_register():
    register_path = os.path.join(frontend_path, "register.html")
    if os.path.exists(register_path):
        return FileResponse(register_path)
    else:
        return {"error": "register.html not found"}

@app.get("/lead/{lead_id}")
async def serve_lead_detail(lead_id: int):
    lead_detail_path = os.path.join(frontend_path, "lead_detail.html")
    if os.path.exists(lead_detail_path):
        return FileResponse(lead_detail_path)
    else:
        return {"error": "lead_detail.html not found"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "LeadIntel API running"}

@app.get("/rules")
async def serve_rules():
    rules_path = os.path.join(frontend_path, "rules.html")
    if os.path.exists(rules_path):
        return FileResponse(rules_path)
    else:
        return {"error": "rules.html not found"}

print("DEBUG: Step 12 - app.py loaded successfully", file=sys.stderr)