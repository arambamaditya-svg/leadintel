import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 50)
    print("LeadIntel Server Starting...")
    print(f"📍 http://localhost:{port}")
    print("=" * 50)
    
    uvicorn.run("app:app", host="0.0.0.0", port=port)