from fastapi import FastAPI

app = FastAPI(title="Render Test")

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "Render deployment is working!"
    }

@app.get("/health")
def health():
    return {
        "healthy": True
    }