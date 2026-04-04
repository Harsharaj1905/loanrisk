from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from environment import LoanRiskEnvironment

app = FastAPI()
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")
env = LoanRiskEnvironment()

class ActionRequest(BaseModel):
    decision: str
    risk_level: str
    failed_criteria: List[str]
    flags: List[str]
    confidence: str

class ResetRequest(BaseModel):
    task: Optional[str] = "easy"

@app.get("/health")
def health():
    return {"status": "ok", "env": "loanrisk_env", "version": "1.0.0"}

@app.get("/tasks")
def tasks():
    return env.get_tasks()

@app.post("/reset")
async def reset(request: Request):
    try:
        body = await request.json()
        task = body.get("task", "easy")
    except Exception:
        task = "easy"
    return env.reset(task)

@app.post("/step")
def step(action: ActionRequest):
    return env.step(action.model_dump())

@app.get("/state")
def state():
    return env.get_state()

@app.get("/")
def root():
    return {"message": "LoanRisk Environment HTTP Server"}

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
