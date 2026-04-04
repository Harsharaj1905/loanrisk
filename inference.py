import os
import json
import requests
from openai import OpenAI

# PyTorch risk scorer — trained on startup
from risk_model import get_risk_score

# Environment variables
API_BASE_URL = os.environ.get("API_BASE_URL", "https://harsha1905-license1905.hf.space")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Groq client via OpenAI-compatible API
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """You are an expert bank loan risk assessment AI.
You analyze loan applications against bank policy and make decisions.

Your decisions must be one of: approve, reject, escalate, request_documents

Rules:
- approve: applicant meets ALL policy requirements
- reject: applicant fails one or more policy requirements with no exceptions
- escalate: borderline case needing human review (co-applicant exceptions, self-employed edge cases, jumbo loans)
- request_documents: missing critical information needed to decide

Risk levels: low, medium, high
Confidence: low, medium, high

You must respond ONLY with valid JSON in this exact format:
{
  "decision": "approve|reject|escalate|request_documents",
  "risk_level": "low|medium|high",
  "failed_criteria": ["list of failed policy criteria, empty if approved"],
  "flags": ["list of notable flags"],
  "confidence": "low|medium|high",
  "reasoning": "brief explanation"
}"""


def get_llm_decision(observation: dict, pytorch_risk_prob: float, pytorch_risk_label: str) -> dict:
    """Use Groq LLM to make a loan decision, informed by PyTorch risk score."""
    profile = observation.get("applicant_profile", {})
    policy = observation.get("bank_policy", {})
    case_id = observation.get("case_id", "unknown")

    income = profile.get("income")
    income_str = f"${income:,}" if isinstance(income, (int, float)) else "N/A (missing)"

    user_prompt = f"""Analyze this loan application and make a decision.

CASE ID: {case_id}

PYTORCH RISK PRE-SCREEN:
- Neural network risk probability: {pytorch_risk_prob:.3f} (0=low risk, 1=high risk)
- Risk label: {pytorch_risk_label}
- Use this as a prior — your final decision may differ based on the full context below.

APPLICANT PROFILE:
- Credit Score: {profile.get('credit_score', 'N/A (missing)')}
- Annual Income: {income_str}
- Employment Type: {profile.get('employment_type', 'N/A')}
- Years Employed: {profile.get('years_employed', 'N/A')}
- Debt Ratio: {profile.get('debt_ratio', 'N/A (missing)')}
- Loan Amount: ${profile.get('loan_amount', 0):,}
- Property Value: ${profile.get('property_value', 0):,}
- LTV Ratio: {round(profile.get('loan_amount', 0) / max(profile.get('property_value', 1), 1), 3)}
- Purpose: {profile.get('purpose', 'N/A')}
- Has Co-Applicant: {profile.get('has_co_applicant', False)}
- Co-Applicant Credit Score: {profile.get('co_applicant_credit_score', 'N/A')}
- Co-Applicant Income: {profile.get('co_applicant_income', 'N/A')}
- Debt Recorded: {profile.get('debt_recorded', 'N/A')}

BANK POLICY:
- Minimum Credit Score: {policy.get('min_credit_score', 650)}
- Maximum Debt Ratio: {policy.get('max_debt_ratio', 0.43)}
- Minimum Years Employed: {policy.get('min_years_employed', 2)}
- Maximum LTV Ratio: {policy.get('max_ltv', 0.8)}
- Co-Applicant Exception Allowed: {policy.get('co_applicant_exception', False)}
- Self-Employed Exception Min Years: {policy.get('self_employed_exception_min_years', 'N/A')}
- Jumbo Loan Threshold: {policy.get('jumbo_loan_threshold', 'N/A')}
- Investment Property Surcharge: {policy.get('investment_property_surcharge', False)}

Analyze carefully. If data is missing (None/N/A), flag it as a failed criterion.
Respond with JSON only."""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        decision = json.loads(raw)
        return decision

    except Exception as e:
        print(f"[LLM ERROR] {e} — using fallback")
        return fallback_decision(profile, policy, pytorch_risk_label)


def fallback_decision(profile: dict, policy: dict, pytorch_label: str = "medium") -> dict:
    """Rule-based fallback if LLM fails."""
    failed = []

    credit = profile.get("credit_score")
    debt_ratio = profile.get("debt_ratio")
    income = profile.get("income")
    years = profile.get("years_employed") or 0
    loan = profile.get("loan_amount") or 0
    value = profile.get("property_value") or 1
    ltv = loan / value if value else 1
    has_co = profile.get("has_co_applicant", False)
    co_exception = policy.get("co_applicant_exception", False)

    if credit is None:
        failed.append("missing_credit_score")
    elif credit < policy.get("min_credit_score", 650):
        failed.append("credit_below_650")

    if debt_ratio is None:
        failed.append("missing_debt_data")
    elif debt_ratio > policy.get("max_debt_ratio", 0.43):
        failed.append("debt_ratio_exceeded")

    if income is None:
        failed.append("missing_primary_income")

    if years < policy.get("min_years_employed", 2):
        failed.append("insufficient_employment_history")

    if ltv > policy.get("max_ltv", 0.8):
        failed.append("ltv_exceeded")

    missing = [f for f in failed if "missing" in f]
    if missing:
        return {"decision": "request_documents", "risk_level": "medium",
                "failed_criteria": failed, "flags": [], "confidence": "high"}

    if not failed:
        return {"decision": "approve", "risk_level": "low",
                "failed_criteria": [], "flags": [], "confidence": "high"}

    if has_co and co_exception and len(failed) == 1:
        return {"decision": "escalate", "risk_level": "medium",
                "failed_criteria": failed, "flags": ["co_applicant_exception_applied"],
                "confidence": "medium"}

    return {"decision": "reject", "risk_level": "high",
            "failed_criteria": failed, "flags": [], "confidence": "high"}


def run_episode(task: str = "easy"):
    """Run a full episode against the environment."""
    base = API_BASE_URL.rstrip("/")
    print(f"[START] task={task}")

    reset_resp = requests.post(f"{base}/reset", json={"task": task})
    obs = reset_resp.json()

    case_id = obs.get("case_id", "unknown")
    total_reward = 0.0
    step_num = 0

    while not obs.get("is_done", False):
        step_num += 1

        profile = obs.get("applicant_profile", {})
        policy = obs.get("bank_policy", {})

        # Step 1: PyTorch pre-screen
        pytorch_prob, pytorch_label = get_risk_score(profile, policy)
        print(f"[STEP] case={case_id} step={step_num} "
              f"pytorch_risk={pytorch_prob} pytorch_label={pytorch_label}")

        # Step 2: LLM decision informed by PyTorch score
        action = get_llm_decision(obs, pytorch_prob, pytorch_label)
        reasoning = action.pop("reasoning", "")

        print(f"[STEP] case={case_id} step={step_num} "
              f"decision={action.get('decision')} "
              f"risk={action.get('risk_level')} "
              f"confidence={action.get('confidence')} "
              f"reasoning={reasoning}")

        # Step 3: Submit to environment
        step_resp = requests.post(f"{base}/step", json=action)
        result = step_resp.json()

        reward = result.get("reward", 0.0)
        done = result.get("done", True)
        total_reward += reward

        print(f"[STEP] reward={reward} done={done} total_reward={total_reward}")

        if done:
            break

        state_resp = requests.get(f"{base}/state")
        obs = state_resp.json()
        obs["case_id"] = case_id

    print(f"[END] case={case_id} total_reward={total_reward} steps={step_num}")
    return total_reward


if __name__ == "__main__":
    print("=== LoanRisk AI Agent — PyTorch + Groq LLM ===")

    tasks = ["easy", "medium", "hard"]
    results = []

    for task in tasks:
        print(f"\n--- Running {task} episode ---")
        try:
            reward = run_episode(task)
            results.append({"task": task, "reward": reward})
        except Exception as e:
            print(f"[ERROR] {task} failed: {e}")
            results.append({"task": task, "reward": 0.0})

    print("\n=== FINAL RESULTS ===")
    for r in results:
        print(f"  {r['task']}: {r['reward']:.2f}")
    avg = sum(r["reward"] for r in results) / len(results)
    print(f"  Average: {avg:.2f}")
