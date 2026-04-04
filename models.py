from pydantic import BaseModel
from typing import Literal, List, Dict, Any

# Graceful fallback if openenv package not installed
try:
    from openenv import Action, Observation, State
except ImportError:
    class Action(BaseModel):
        pass
    class Observation(BaseModel):
        pass
    class State(BaseModel):
        pass

class LoanAction(Action):
    decision: Literal["approve", "reject", "escalate", "request_documents"]
    risk_level: Literal["low", "medium", "high"]
    failed_criteria: List[str]
    flags: List[str]
    confidence: Literal["high", "medium", "low"]

class LoanObservation(Observation):
    case_id: str
    stage: int
    applicant_profile: Dict[str, Any]
    bank_policy: Dict[str, Any]
    available_decisions: List[str]
    feedback: str
    partial_score: float
    flags_raised: List[str]
    task_description: str

class LoanState(State):
    case_id: str
    difficulty: str
    accumulated_reward: float = 0.0
    is_done: bool = False
