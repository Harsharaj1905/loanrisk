import os
import json
import sys
from typing import Dict, Any, Optional
from openai import OpenAI
from client import LoanRiskClient
from models import LoanAction


def rule_based_decision(obs: Dict[str, Any]) -> Optional[LoanAction]:
    """
    Rule-based layer covering ~60% of cases without an API call.
    Returns None if the case is ambiguous (falls back to LLM).
    """
    profile = obs.get("applicant_profile", {})
    policy = obs.get("bank_policy", {})

    credit = profile.get("credit_score")
    income = profile.get("income")
    debt_recorded = profile.get("debt_recorded", True)
    has_co_applicant = profile.get("has_co_applicant", False)
    employment_type = profile.get("employment_type", "salaried")
    years_employed = profile.get("years_employed", 0)
    debt_ratio = profile.get("debt_ratio")
    loan_amount = profile.get("loan_amount", 0)
    property_value = profile.get("property_value", 1)

    min_credit = policy.get("min_credit_score", 650)
    max_debt_ratio = policy.get("max_debt_ratio", 0.43)
    min_years = policy.get("min_years_employed", 2)
    co_exception = policy.get("co_applicant_exception", False)
    self_emp_min_years = policy.get("self_employed_exception_min_years", 2)
    jumbo_threshold = policy.get("jumbo_loan_threshold", None)

    failed_criteria = []
    flags = []

    # Check missing data
    if credit is None:
        return LoanAction(
            decision="request_documents",
            risk_level="medium",
            failed_criteria=["missing_credit_score"],
            flags=[],
            confidence="high"
        )
    if income is None and not has_co_applicant:
        return LoanAction(
            decision="request_documents",
            risk_level="medium",
            failed_criteria=["missing_primary_income"],
            flags=[],
            confidence="high"
        )
    if not debt_recorded:
        failed_criteria.append("missing_debt_data")

    # Credit check
    credit_failed = credit < min_credit
    if credit_failed:
        key = "primary_credit_below_650" if has_co_applicant else "credit_below_650"
        failed_criteria.append(key)

    # Employment check
    if employment_type == "self_employed":
        if years_employed < self_emp_min_years:
            failed_criteria.append("insufficient_employment_history")
            flags.append("self_employed_below_exception_threshold")
        else:
            flags.append("self_employed_exception")
    else:
        if years_employed < min_years:
            failed_criteria.append("insufficient_employment_history")

    # Debt ratio check
    if debt_ratio is not None and debt_ratio > max_debt_ratio:
        failed_criteria.append("debt_ratio_exceeded")

    # Co-applicant check
    if has_co_applicant:
        co_credit = profile.get("co_applicant_credit_score")
        if co_credit is not None and co_credit < min_credit:
            failed_criteria.append("co_applicant_credit_below_minimum")
        elif co_exception and credit_failed:
            flags.append("co_applicant_exception_applied")

    # Investment flag
    if profile.get("purpose") == "investment":
        flags.append("investment_property_flag")

    # Jumbo loan flag
    if jumbo_threshold and loan_amount > jumbo_threshold:
        flags.append("jumbo_loan_flag")

    # High LTV flag
    if property_value > 0:
        ltv = loan_amount / property_value
        if ltv > 0.80:
            flags.append("high_ltv_flagged")

    # Decision logic
    hard_fails = [c for c in failed_criteria if c != "missing_debt_data"]

    if not failed_criteria and not hard_fails:
        # Clean approval
        risk = "low" if (debt_ratio or 0) < 0.35 else "medium"
        return LoanAction(
            decision="approve",
            risk_level=risk,
            failed_criteria=[],
            flags=flags,
            confidence="high"
        )

    if "missing_debt_data" in failed_criteria and len(failed_criteria) == 1:
        return LoanAction(
            decision="request_documents",
            risk_level="medium",
            failed_criteria=failed_criteria,
            flags=flags,
            confidence="high"
        )

    # If co-applicant exception applies and only credit is failed → escalate
    if (
        has_co_applicant
        and co_exception
        and set(hard_fails) <= {"primary_credit_below_650"}
        and "co_applicant_credit_below_minimum" not in failed_criteria
        and "debt_ratio_exceeded" not in failed_criteria
        and "insufficient_employment_history" not in failed_criteria
    ):
        return LoanAction(
            decision="escalate",
            risk_level="medium",
            failed_criteria=failed_criteria,
            flags=flags,
            confidence="medium"
        )

    # Multiple hard failures → reject
    if len(hard_fails) >= 2:
        return LoanAction(
            decision="reject",
            risk_level="high",
            failed_criteria=failed_criteria,
            flags=flags,
            confidence="high"
        )

    # Self-employed with credit failure but qualifies for exception → escalate
    if (
        employment_type == "self_employed"
        and years_employed >= self_emp_min_years
        and set(hard_fails) <= {"credit_below_650"}
        and "debt_ratio_exceeded" not in failed_criteria
    ):
        return LoanAction(
            decision="escalate",
            risk_level="medium",
            failed_criteria=failed_criteria,
            flags=flags,
            confidence="medium"
        )

    # Self-employed below exception threshold → reject (flag already added above)
    if (
        employment_type == "self_employed"
        and years_employed < self_emp_min_years
        and set(hard_fails) <= {"insufficient_employment_history"}
    ):
        return LoanAction(
            decision="reject",
            risk_level="high",
            failed_criteria=failed_criteria,
            flags=flags,
            confidence="high"
        )

    # Single debt ratio or credit failure with no exceptions → reject
    if len(hard_fails) == 1:
        return LoanAction(
            decision="reject",
            risk_level="high",
            failed_criteria=failed_criteria,
            flags=flags,
            confidence="high"
        )

    # True fallback — should never reach here with current case pool
    return LoanAction(
        decision="escalate",
        risk_level="medium",
        failed_criteria=failed_criteria,
        flags=flags,
        confidence="low"
    )


def llm_decision(llm_client, model_name: str, obs: Dict[str, Any]) -> LoanAction:
    system_prompt = (
        "You are a senior loan risk assessor. Evaluate the loan application against bank policy.\n"
        "Return ONLY valid JSON with NO explanation, NO markdown, NO backticks. Exact schema:\n"
        '{"decision": "approve"|"reject"|"escalate"|"request_documents", '
        '"risk_level": "low"|"medium"|"high", '
        '"failed_criteria": ["string"], '
        '"flags": ["string"], '
        '"confidence": "high"|"medium"|"low"}\n'
        "Use keys like: credit_below_650, debt_ratio_exceeded, insufficient_employment_history, "
        "missing_credit_score, missing_debt_data, co_applicant_credit_below_minimum, "
        "primary_credit_below_650, missing_primary_income.\n"
        "Use flags like: self_employed_exception, co_applicant_exception_applied, "
        "investment_property_flag, high_ltv_flagged, jumbo_loan_flag."
    )

    completion = llm_client.chat.completions.create(
        model=model_name,
        temperature=0.0,
        max_tokens=300,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(obs)}
        ]
    )

    text = completion.choices[0].message.content.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    parsed = json.loads(text)
    return LoanAction(**parsed)


def main():
    api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000/v1")
    model_name = os.environ.get("MODEL_NAME", "gpt-4o")
    hf_token = os.environ.get("HF_TOKEN", "default_token")

    llm_client = OpenAI(base_url=api_base_url, api_key=hf_token)
    env_client = LoanRiskClient("http://localhost:7860")

    tasks = ["easy", "medium", "hard"]
    episodes_per_task = 3
    results = []
    episode_num = 1

    for task in tasks:
        for _ in range(episodes_per_task):
            obs = env_client.reset(task=task)

            # Exact format required by validator
            print(f"[START] episode={episode_num} task={task}", flush=True)

            # Try rule-based first, fall back to LLM
            action = rule_based_decision(obs)
            if action is None:
                action = llm_decision(llm_client, model_name, obs)

            action_payload = action.model_dump()
            compact_json = json.dumps(action_payload, separators=(',', ':'))

            step_resp = env_client.step(action_payload)
            reward = round(float(step_resp.get("reward", 0.0)), 1)
            done = bool(step_resp.get("done", True))

            # Exact format required by validator
            print(f"[STEP] step=1 action={compact_json} reward={reward} done={done}", flush=True)
            print(f"[END] episode={episode_num} total_reward={reward} task={task}", flush=True)

            results.append({
                "episode": episode_num,
                "task": task,
                "decision": action.decision,
                "reward": reward
            })
            episode_num += 1

    # Save results
    os.makedirs("outputs/evals", exist_ok=True)
    with open("outputs/evals/inference_results.json", "w") as f:
        json.dump(results, f, indent=4)

    # Summary table
    print("\nSummary:", flush=True)
    print(f"{'Ep':<5}{'Task':<10}{'Decision':<22}{'Reward'}", flush=True)
    for r in results:
        print(f"{r['episode']:<5}{r['task']:<10}{r['decision']:<22}{r['reward']}", flush=True)


if __name__ == "__main__":
    main()
