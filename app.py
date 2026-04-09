from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from environment import LoanRiskEnvironment

app = FastAPI()

try:
    app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")
except Exception:
    pass

env = LoanRiskEnvironment()


class ActionRequest(BaseModel):
    decision: str
    risk_level: str
    failed_criteria: List[str]
    flags: List[str]
    confidence: str


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

    state = env.reset(task)

    # ✅ OpenEnv spec requires this exact wrapper
    return JSONResponse(content={
        "observation": state,
        "info": {"task": task}
    })


@app.post("/step")
def step(action: ActionRequest):
    result = env.step(action.model_dump())

    # ✅ OpenEnv spec requires observation in step response too
    return JSONResponse(content={
        "observation": env.get_state(),
        "reward": result.get("reward", 0.0),
        "done": result.get("done", True),
        "info": result.get("info", {})
    })


@app.get("/state")
def state():
    return JSONResponse(content={
        "observation": env.get_state(),
        "info": {}
    })


@app.get("/validate")
def validate():
    # ✅ Required by "openenv validate" check
    return {
        "env_name": "loanrisk",
        "version": "1.0.0",
        "actions": ["approve", "reject", "escalate", "request_documents"],
        "observation_space": "loan_application",
        "reward_range": [0.0, 1.0]
    }


@app.get("/")
def root():
    return {"message": "LoanRisk Environment HTTP Server"}
