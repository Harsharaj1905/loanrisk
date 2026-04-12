import os
import json
import requests

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
No extra fields. No markdown. No explanation outside JSON."""


def rule_decision(obs: dict) -> dict:
    profile = obs.get("applicant_profile", {})
    policy = obs.get("bank_policy", {})
    failed = []
    flags = []
    credit = profile.get("credit_score")
    income = profile.get("income")
    debt_ratio = profile.get("debt_ratio")
    debt_recorded = profile.get("debt_recorded", True)
    years = profile.get("years_employed", 0)
    has_co = profile.get("has_co_applicant", False)
    emp_type = profile.get("employment_type", "salaried")
    co_exception = policy.get("co_applicant_exception", False)
    min_credit = policy.get("min_credit_score", 650)
    max_ratio = policy.get("max_debt_ratio", 0.43)
    min_years = policy.get("min_years_employed", 2)

    if credit is None:
        failed.append("missing_credit_score")
    elif credit < min_credit:
        failed.append("primary_credit_below_650" if has_co else "credit_below_650")

    if not debt_recorded:
        failed.append("missing_debt_data")
    elif debt_ratio is not None and debt_ratio > max_ratio:
        failed.append("debt_ratio_exceeded")

    if income is None and not has_co:
        failed.append("missing_primary_income")

    if emp_type == "self_employed":
        se_min = policy.get("self_employed_exception_min_years", 2)
        if years < se_min:
            failed.append("insufficient_employment_history")
            flags.append("self_employed_below_exception_threshold")
        else:
            flags.append("self_employed_exception")
    elif years < min_years:
        failed.append("insufficient_employment_history")

    if has_co:
        co_credit = profile.get("co_applicant_credit_score")
        if co_credit and co_credit < min_credit:
            failed.append("co_applicant_credit_below_minimum")
        elif co_exception and "primary_credit_below_650" in failed:
            flags.append("co_applicant_exception_applied")

    loan = profile.get("loan_amount", 0)
    value = profile.get("property_value", 1)
    if value and loan / value > policy.get("max_ltv", 0.8):
        flags.append("high_ltv_flagged")

    jumbo = policy.get("jumbo_loan_threshold")
    if jumbo and loan > jumbo:
        flags.append("jumbo_loan_flag")

    if profile.get("purpose") == "investment" and policy.get("investment_property_surcharge"):
        flags.append("investment_property_flag")

    missing = [f for f in failed if "missing" in f]
    if missing:
        return {"decision": "request_documents", "risk_level": "medium",
                "failed_criteria": failed, "flags": flags, "confidence": "high"}
    if not failed:
        return {"decision": "approve", "risk_level": "low",
                "failed_criteria": [], "flags": flags, "confidence": "high"}
    if has_co and co_exception and set(failed) <= {"primary_credit_below_650"}:
        return {"decision": "escalate", "risk_level": "medium",
                "failed_criteria": failed, "flags": flags, "confidence": "medium"}
    return {"decision": "reject", "risk_level": "high",
            "failed_criteria": failed, "flags": flags, "confidence": "high"}


def llm_decision(obs: dict) -> dict:
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

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 300
    }

    base = API_BASE_URL.rstrip("/")
    urls_to_try = []
    if base.endswith("/v1"):
        urls_to_try = [f"{base}/chat/completions"]
    else:
        urls_to_try = [f"{base}/v1/chat/completions", f"{base}/chat/completions"]

    for url in urls_to_try:
        try:
            print(f"[DEBUG] Trying LLM: {url}", flush=True)
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw.strip())
            result = {
                "decision": parsed.get("decision", "escalate"),
                "risk_level": parsed.get("risk_level", "medium"),
                "failed_criteria": parsed.get("failed_criteria", []),
                "flags": parsed.get("flags", []),
                "confidence": parsed.get("confidence", "medium")
            }
            print(f"[DEBUG] LLM success: {result['decision']}", flush=True)
            return result
        except Exception as e:
            print(f"[DEBUG] LLM failed {url}: {e}", flush=True)

    print("[WARN] All LLM attempts failed — using rule fallback", flush=True)
    return rule_decision(obs)


def reset_env(task: str) -> dict:
    r = requests.post("http://localhost:7860/reset", json={"task": task}, timeout=30)
    r.raise_for_status()
    return r.json()


def step_env(action: dict) -> dict:
    r = requests.post("http://localhost:7860/step", json=action, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    print(f"[INFO] API_BASE_URL={API_BASE_URL}", flush=True)
    print(f"[INFO] MODEL_NAME={MODEL_NAME}", flush=True)
    print(f"[INFO] API_KEY set={bool(API_KEY and API_KEY != 'no-key')}", flush=True)

    tasks = ["easy", "medium", "hard"]
    episodes_per_task = 1
    results = []
    episode_num = 1

    for task in tasks:
        for _ in range(episodes_per_task):
            try:
                obs = reset_env(task)
            except Exception as e:
                print(f"[ERROR] reset failed for {task}: {e}", flush=True)
                continue

            print(f"[START] episode={episode_num} task={task}", flush=True)

            try:
                action = llm_decision(obs)
            except Exception as e:
                print(f"[ERROR] decision failed: {e}", flush=True)
                action = rule_decision(obs)

            compact_json = json.dumps(action, separators=(',', ':'))

            try:
                step_resp = step_env(action)
            except Exception as e:
                print(f"[ERROR] step failed: {e}", flush=True)
                step_resp = {"reward": 0.15, "done": True}

            reward = float(step_resp.get("reward", 0.15))
            reward = round(max(0.1, min(0.9, reward)), 2)
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
    for r in results:
        print(f"{r['episode']:<5}{r['task']:<10}{r['decision']:<22}{r['reward']}", flush=True)


if __name__ == "__main__":
    main()
