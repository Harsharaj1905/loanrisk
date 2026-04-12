import random
from typing import Dict, Any

CASE_POOLS = {
    "easy": [
        {
            "case_id": "easy_001",
            "applicant": {
                "credit_score": 780, "income": 95000, "has_co_applicant": False,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 6, "debt_ratio": 0.18, "loan_amount": 200000,
                "property_value": 400000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80
            },
            "gold": {
                "valid_decisions": ["approve"], "risk_level": "low",
                "required_failed_criteria": [], "required_flags": []
            }
        },
        {
            "case_id": "easy_002",
            "applicant": {
                "credit_score": 520, "income": 42000, "has_co_applicant": False,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 3, "debt_ratio": 0.55, "loan_amount": 180000,
                "property_value": 220000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80
            },
            "gold": {
                "valid_decisions": ["reject"], "risk_level": "high",
                "required_failed_criteria": ["credit_below_650", "debt_ratio_exceeded"],
                "required_flags": []
            }
        },
        {
            "case_id": "easy_003",
            "applicant": {
                "credit_score": 700, "income": 65000, "has_co_applicant": False,
                "debt_recorded": False, "employment_type": "salaried",
                "years_employed": 4, "debt_ratio": None, "loan_amount": 150000,
                "property_value": 300000, "purpose": "refinance"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80
            },
            "gold": {
                "valid_decisions": ["request_documents"], "risk_level": "medium",
                "required_failed_criteria": ["missing_debt_data"], "required_flags": []
            }
        },
        {
            "case_id": "easy_004",
            "applicant": {
                "credit_score": 810, "income": 120000, "has_co_applicant": False,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 10, "debt_ratio": 0.25, "loan_amount": 300000,
                "property_value": 600000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80
            },
            "gold": {
                "valid_decisions": ["approve"], "risk_level": "low",
                "required_failed_criteria": [], "required_flags": []
            }
        },
        {
            "case_id": "easy_005",
            "applicant": {
                "credit_score": 600, "income": 55000, "has_co_applicant": False,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 1, "debt_ratio": 0.38, "loan_amount": 140000,
                "property_value": 200000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80
            },
            "gold": {
                "valid_decisions": ["reject"], "risk_level": "high",
                "required_failed_criteria": ["credit_below_650", "insufficient_employment_history"],
                "required_flags": []
            }
        },
    ],
    "medium": [
        {
            "case_id": "medium_001",
            "applicant": {
                "credit_score": 630, "income": 78000, "has_co_applicant": True,
                "co_applicant_credit_score": 720, "co_applicant_income": 52000,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 3, "debt_ratio": 0.41, "loan_amount": 250000,
                "property_value": 350000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80, "co_applicant_exception": True
            },
            "gold": {
                "valid_decisions": ["approve", "escalate"], "risk_level": "medium",
                "required_failed_criteria": ["primary_credit_below_650"],
                "required_flags": ["co_applicant_exception_applied"]
            }
        },
        {
            "case_id": "medium_002",
            "applicant": {
                "credit_score": 640, "income": 92000, "has_co_applicant": False,
                "debt_recorded": True, "employment_type": "self_employed",
                "years_employed": 3, "debt_ratio": 0.28, "loan_amount": 200000,
                "property_value": 380000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80,
                "self_employed_exception_min_years": 2
            },
            "gold": {
                "valid_decisions": ["escalate"], "risk_level": "medium",
                "required_failed_criteria": ["credit_below_650"],
                "required_flags": ["self_employed_exception"]
            }
        },
        {
            "case_id": "medium_003",
            "applicant": {
                "credit_score": 720, "income": 48000, "has_co_applicant": False,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 5, "debt_ratio": 0.45, "loan_amount": 160000,
                "property_value": 220000, "purpose": "refinance"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80
            },
            "gold": {
                "valid_decisions": ["reject"], "risk_level": "high",
                "required_failed_criteria": ["debt_ratio_exceeded"], "required_flags": []
            }
        },
        {
            "case_id": "medium_004",
            "applicant": {
                "credit_score": None, "income": 85000, "has_co_applicant": False,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 8, "debt_ratio": 0.30, "loan_amount": 220000,
                "property_value": 400000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80
            },
            "gold": {
                "valid_decisions": ["request_documents"], "risk_level": "medium",
                "required_failed_criteria": ["missing_credit_score"], "required_flags": []
            }
        },
        {
            "case_id": "medium_005",
            "applicant": {
                "credit_score": 680, "income": 110000, "has_co_applicant": False,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 4, "debt_ratio": 0.35, "loan_amount": 400000,
                "property_value": 480000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80
            },
            "gold": {
                "valid_decisions": ["approve"], "risk_level": "medium",
                "required_failed_criteria": [], "required_flags": ["high_ltv_flagged"]
            }
        },
    ],
    "hard": [
        {
            "case_id": "hard_001",
            "applicant": {
                "credit_score": 610, "income": None, "has_co_applicant": True,
                "co_applicant_credit_score": 680, "co_applicant_income": 95000,
                "debt_recorded": True, "employment_type": "self_employed",
                "years_employed": 4, "debt_ratio": 0.39, "loan_amount": 280000,
                "property_value": 360000, "purpose": "investment"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80,
                "co_applicant_exception": True,
                "self_employed_exception_min_years": 2,
                "investment_property_surcharge": True
            },
            "gold": {
                "valid_decisions": ["escalate"], "risk_level": "high",
                "required_failed_criteria": ["primary_credit_below_650", "missing_primary_income"],
                "required_flags": ["co_applicant_exception_applied", "self_employed_exception", "investment_property_flag"]
            }
        },
        {
            "case_id": "hard_002",
            "applicant": {
                "credit_score": 590, "income": 62000, "has_co_applicant": False,
                "debt_recorded": False, "employment_type": "contract",
                "years_employed": 1, "debt_ratio": None, "loan_amount": 190000,
                "property_value": 230000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80
            },
            "gold": {
                "valid_decisions": ["reject"], "risk_level": "high",
                "required_failed_criteria": ["credit_below_650", "missing_debt_data", "insufficient_employment_history"],
                "required_flags": []
            }
        },
        {
            "case_id": "hard_003",
            "applicant": {
                "credit_score": 660, "income": 75000, "has_co_applicant": True,
                "co_applicant_credit_score": 500, "co_applicant_income": 30000,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 5, "debt_ratio": 0.48, "loan_amount": 310000,
                "property_value": 400000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80, "co_applicant_exception": True
            },
            "gold": {
                "valid_decisions": ["reject"], "risk_level": "high",
                "required_failed_criteria": ["debt_ratio_exceeded", "co_applicant_credit_below_minimum"],
                "required_flags": []
            }
        },
        {
            "case_id": "hard_004",
            "applicant": {
                "credit_score": 670, "income": 88000, "has_co_applicant": False,
                "debt_recorded": True, "employment_type": "self_employed",
                "years_employed": 1, "debt_ratio": 0.37, "loan_amount": 240000,
                "property_value": 320000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80,
                "self_employed_exception_min_years": 2
            },
            "gold": {
                "valid_decisions": ["reject"], "risk_level": "high",
                "required_failed_criteria": ["insufficient_employment_history"],
                "required_flags": ["self_employed_below_exception_threshold"]
            }
        },
        {
            "case_id": "hard_005",
            "applicant": {
                "credit_score": 645, "income": 130000, "has_co_applicant": True,
                "co_applicant_credit_score": 710, "co_applicant_income": 85000,
                "debt_recorded": True, "employment_type": "salaried",
                "years_employed": 7, "debt_ratio": 0.42, "loan_amount": 500000,
                "property_value": 620000, "purpose": "home_purchase"
            },
            "bank_policy": {
                "min_credit_score": 650, "max_debt_ratio": 0.43,
                "min_years_employed": 2, "max_ltv": 0.80,
                "co_applicant_exception": True, "jumbo_loan_threshold": 450000
            },
            "gold": {
                "valid_decisions": ["escalate"], "risk_level": "medium",
                "required_failed_criteria": ["primary_credit_below_650"],
                "required_flags": ["co_applicant_exception_applied", "jumbo_loan_flag"]
            }
        },
    ]
}

FALLBACK_CASE = {
    "case_id": "fallback_001",
    "applicant": {
        "credit_score": 720, "income": 80000, "has_co_applicant": False,
        "debt_recorded": True, "employment_type": "salaried",
        "years_employed": 5, "debt_ratio": 0.30, "loan_amount": 200000,
        "property_value": 400000, "purpose": "home_purchase"
    },
    "bank_policy": {
        "min_credit_score": 650, "max_debt_ratio": 0.43,
        "min_years_employed": 2, "max_ltv": 0.80
    },
    "gold": {
        "valid_decisions": ["approve"], "risk_level": "low",
        "required_failed_criteria": [], "required_flags": []
    }
}


def _safe_reward(r) -> float:
    """Guarantee reward is strictly between 0.0 and 1.0 — never equal to either boundary."""
    try:
        r = float(r)
    except Exception:
        return 0.15
    if r <= 0.0 or r != r:  # catches 0.0 and NaN
        return 0.15
    if r >= 1.0:
        return 0.85
    return round(max(0.11, min(0.89, r)), 2)


class LoanRiskEnvironment:
    def __init__(self):
        self.current_task = "easy"
        self.current_case = dict(FALLBACK_CASE)
        self.accumulated_reward = 0.15
        self.decisions_so_far = []
        self.is_done = False

    def get_tasks(self) -> list:
        return [
            {"id": "easy", "description": "Single applicant, clear-cut case", "difficulty": "easy"},
            {"id": "medium", "description": "Exception clauses must be evaluated", "difficulty": "medium"},
            {"id": "hard", "description": "Missing data, co-applicants, overlapping exceptions", "difficulty": "hard"},
        ]

    def reset(self, task: str = "easy") -> Dict[str, Any]:
        self.current_task = task if task in CASE_POOLS else "easy"
        pool = CASE_POOLS.get(self.current_task, CASE_POOLS["easy"])
        self.current_case = random.choice(pool)
        self.is_done = False
        self.accumulated_reward = 0.15  # Safe non-zero baseline
        self.decisions_so_far = []
        return self.get_state()

    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.decisions_so_far.append(action)
            gold = self.current_case.get("gold", {})

            # Start with safe baseline — never 0.0
            reward = 0.15

            valid_decisions = gold.get("valid_decisions", [])
            if valid_decisions and action.get("decision") in valid_decisions:
                reward += 0.40

            gold_risk = gold.get("risk_level", "")
            if gold_risk and action.get("risk_level") == gold_risk:
                reward += 0.20

            agent_criteria = set(action.get("failed_criteria") or [])
            gold_criteria = set(gold.get("required_failed_criteria") or [])
            matched = agent_criteria & gold_criteria
            reward += min(len(matched), 3) * 0.10

            hallucinated = agent_criteria - gold_criteria
            reward -= len(hallucinated) * 0.02

            agent_flags = set(action.get("flags") or [])
            gold_flags = set(gold.get("required_flags") or [])
            if gold_flags:
                if agent_flags >= gold_flags:
                    reward += 0.10
            else:
                if not agent_flags:
                    reward += 0.10

            reward = _safe_reward(reward)

        except Exception:
            reward = 0.15

        self.accumulated_reward = reward
        self.is_done = True
        return {"reward": reward, "done": True, "info": {}}

    def get_state(self) -> Dict[str, Any]:
        try:
            case = self.current_case
            return {
                "case_id": case.get("case_id", "unknown"),
                "stage": 1,
                "applicant_profile": case.get("applicant", {}),
                "bank_policy": case.get("bank_policy", {}),
                "available_decisions": ["approve", "reject", "escalate", "request_documents"],
                "feedback": "",
                "partial_score": _safe_reward(self.accumulated_reward),
                "flags_raised": [],
                "task_description": f"Evaluate this {self.current_task} loan application against bank policy.",
                "is_done": self.is_done
            }
        except Exception:
            return {
                "case_id": "error", "stage": 1,
                "applicant_profile": {}, "bank_policy": {},
                "available_decisions": ["approve", "reject", "escalate", "request_documents"],
                "feedback": "", "partial_score": 0.15,
                "flags_raised": [], "task_description": "Evaluate this loan application.",
                "is_done": False
            }
