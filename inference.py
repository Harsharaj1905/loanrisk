import os
import json
from openai import OpenAI
from client import LoanRiskClient

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o")
API_KEY = os.environ.get("API_KEY") or os.environ.get("HF_TOKEN", "no-key")

SYSTEM_PROMPT = """You are an expert bank loan risk assessment AI.
Analyze the loan application against bank policy and respond ONLY with valid JSON:
{
  "decision": "approve|reject|escalate|request_documents",
  "risk_level": "low|medium|high",
  "failed_criteria": ["list of failed criteria, empty if none"],
  "flags": ["list of flags, empty if none"],
  "confidence": "low|medium|high"
}

Rules:
- approve: applicant meets ALL policy requirements
- reject: applicant fails requirements with no exceptions
- escalate: borderline case needing human review
- request_documents: missing critical information

Failed criteria keys: credit_below_650, debt_ratio_exceeded, insufficient_employment_history,
missing_credit_score, missing_debt_data, missing_primary_income, co_applicant_credit_below_minimum,
primary_credit_below_650, ltv_exceeded

Flag keys: co_applicant_exception_applied, self_employed_exception,
self_employed_below_exception_threshold, investment_property_flag, jumbo_loan_flag, high_ltv_flagged

No extra fields. No markdown. No explanation outside JSON."""


def llm_decision(client, obs: dict) -> dict:
    profile = obs.get("applicant_profile", {})
    policy = obs.get("bank_policy", {})

    income = profile.get("income")
    income_str = f"${income:,}" if isinstance(income, (int, float)) else "N/A (missing)"

    user_prompt = f"""Evaluate this loan application:

APPLICANT:
- Credit Score: {profile.get('credit_score', 'N/A (missing)')}
- Annual Income: {income_str}
- Employment Type: {profile.get('employment_type', 'N/A')}
- Years Employed: {profile.get('years_employed', 'N/A')}
- Debt Ratio: {profile.get('debt_ratio', 'N/A (missing)')}
- Loan Amount: {profile.get('loan_amount', 0)}
- Property Value: {profile.get('property_value', 0)}
- Purpose: {profile.get('purpose', 'N/A')}
- Has Co-Applicant: {profile.get('has_co_applicant', False)}
- Co-Applicant Credit Score: {profile.get('co_applicant_credit_score', 'N/A')}
- Co-Applicant Income: {profile.get('co_applicant_income', 'N/A')}
- Debt Recorded: {profile.get('debt_recorded', True)}

BANK POLICY:
- Min Credit Score: {policy.get('min_credit_score', 650)}
- Max Debt Ratio: {policy.get('max_debt_ratio', 0.43)}
- Min Years Employed: {policy.get('min_years_employed', 2)}
- Max LTV: {policy.get('max_ltv', 0.8)}
- Co-Applicant Exception: {policy.get('co_applicant_exception', False)}
- Self-Employed Exception Min Years: {policy.get('self_employed_exception_min_years', 'N/A')}
- Jumbo Loan Threshold: {policy.get('jumbo_loan_threshold', 'N/A')}
- Investment Property Surcharge: {policy.get('investment_property_surcharge', False)}

Respond with JSON only."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=300
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    parsed = json.loads(raw)
    return {
        "decision": parsed.get("decision", "escalate"),
        "risk_level": parsed.get("risk_level", "medium"),
        "failed_criteria": parsed.get("failed_criteria", []),
        "flags": parsed.get("flags", []),
        "confidence": parsed.get("confidence", "medium")
    }


def main():
    llm_client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY
    )

    env_client = LoanRiskClient("http://localhost:7860")

    tasks = ["easy", "medium", "hard"]
    episodes_per_task = 3
    results = []
    episode_num = 1

    for task in tasks:
        for _ in range(episodes_per_task):
            obs = env_client.reset(task=task)
            print(f"[START] episode={episode_num} task={task}", flush=True)

            action = llm_decision(llm_client, obs)
            compact_json = json.dumps(action, separators=(',', ':'))

            step_resp = env_client.step(action)
            reward = round(float(step_resp.get("reward", 0.0)), 1)
            done = bool(step_resp.get("done", True))

            print(f"[STEP] step=1 action={compact_json} reward={reward} done={done}", flush=True)
            print(f"[END] episode={episode_num} total_reward={reward} task={task}", flush=True)

            results.append({
                "episode": episode_num,
                "task": task,
                "decision": action["decision"],
                "reward": reward
            })
            episode_num += 1

    os.makedirs("outputs/evals", exist_ok=True)
    with open("outputs/evals/inference_results.json", "w") as f:
        json.dump(results, f, indent=4)

    print("\nSummary:", flush=True)
    print(f"{'Ep':<5}{'Task':<10}{'Decision':<22}{'Reward'}", flush=True)
    for r in results:
        print(f"{r['episode']:<5}{r['task']:<10}{r['decision']:<22}{r['reward']}", flush=True)


if __name__ == "__main__":
    main()
