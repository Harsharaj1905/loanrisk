import random
from typing import Dict, Any, List

# Real case pools with varied gold answers — fixes the "every reward = 0.7" bug
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
                "valid_decisions": ["approve"],
                "risk_level": "low",
                "required_failed_criteria": [],
                "required_flags": []
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
                "valid_decisions": ["reject"],
                "risk_level": "high",
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
                "valid_decisions": ["request_documents"],
                "risk_level": "medium",
                "required_failed_criteria": ["missing_debt_data"],
                "required_flags": []
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
                "valid_decisions": ["approve"],
                "risk_level": "low",
                "required_failed_criteria": [],
                "required_flags": []
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
                "valid_decisions": ["reject"],
                "risk_level": "high",
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
                "min_years_employed": 2, "max_ltv": 0.80,
                "co_applicant_exception": True
            },
            "gold": {
                "valid_decisions": ["approve", "escalate"],
                "risk_level": "medium",
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
                "valid_decisions": ["escalate"],
                "risk_level": "medium",
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
                "valid_decisions": ["reject"],
                "risk_level": "high",
                "required_failed_criteria": ["debt_ratio_exceeded"],
                "required_flags": []
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
                "valid_decisions": ["request_documents"],
                "risk_level": "medium",
                "required_failed_criteria": ["missing_credit_score"],
                "required_flags": []
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
                "valid_decisions": ["approve"],
                "risk_level": "medium",
                "required_failed_criteria": [],
                "required_flags": ["high_ltv_flagged"]
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
                "valid_decisions": ["escalate"],
                "risk_level": "high",
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
                "valid_decisions": ["reject"],
                "risk_level": "high",
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
                "min_years_employed": 2, "max_ltv": 0.80,
                "co_applicant_exception": True
            },
            "gold": {
                "valid_decisions": ["reject"],
                "risk_level": "high",
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
                "valid_decisions": ["reject"],
                "risk_level": "high",
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
                "co_applicant_exception": True,
                "jumbo_loan_threshold": 450000
            },
            "gold": {
                "valid_decisions": ["escalate"],
                "risk_level": "medium",
                "required_failed_criteria": ["primary_credit_below_650"],
                "required_flags": ["co_applicant_exception_applied", "jumbo_loan_flag"]
            }
        },
    ]
}


class LoanRiskEnvironment:
    def __init__(self):
        self.current_task = ""
        self.current_case = {}
        self.accumulated_reward = 0.0
        self.decisions_so_far = []
        self.is_done = False

    def get_tasks(self) -> list[dict]:
        return [
            {"id": "easy", "description": "Single applicant, clear-cut case", "difficulty": "easy"},
            {"id": "medium", "description": "Exception clauses must be evaluated", "difficulty": "medium"},
            {"id": "hard", "description": "Missing data, co-applicants, overlapping exceptions", "difficulty": "hard"},
        ]

    def reset(self, task: str) -> Dict[str, Any]:
        self.current_task = task
        pool = CASE_POOLS.get(task, CASE_POOLS["easy"])
        self.current_case = random.choice(pool)
        self.is_done = False
        self.accumulated_reward = 0.0
        self.decisions_so_far = []
        return self.get_state()

    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        self.decisions_so_far.append(action)
        gold = self.current_case["gold"]
        reward = 0.0

        # +0.40 correct decision
        if action.get("decision") in gold["valid_decisions"]:
            reward += 0.40

        # +0.20 correct risk level
        if action.get("risk_level") == gold.get("risk_level"):
            reward += 0.20

        # +0.10 per correct failed criterion (max 3 = 0.30)
        agent_criteria = set(action.get("failed_criteria", []))
        gold_criteria = set(gold.get("required_failed_criteria", []))
        matched = agent_criteria & gold_criteria
        reward += min(len(matched), 3) * 0.10

        # -0.05 per hallucinated criterion
        hallucinated = agent_criteria - gold_criteria
        reward -= len(hallucinated) * 0.05

        # +0.10 flags correct
        agent_flags = set(action.get("flags", []))
        gold_flags = set(gold.get("required_flags", []))
        if gold_flags:
            if agent_flags >= gold_flags:
                reward += 0.10
        else:
            if not agent_flags:
                reward += 0.10

        reward = round(max(0.05, min(0.95, reward)), 2)
        self.accumulated_reward = reward
        self.is_done = True

        return {"reward": reward, "done": True, "info": {}}

    def get_state(self) -> Dict[str, Any]:
        case = self.current_case
        return {
            "case_id": case.get("case_id", "unknown"),
            "stage": 1,
            "applicant_profile": case.get("applicant", {}),
            "bank_policy": case.get("bank_policy", {}),
            "available_decisions": ["approve", "reject", "escalate", "request_documents"],
            "feedback": "",
            "partial_score": round(self.accumulated_reward, 2),
            "flags_raised": [],
            "task_description": f"Evaluate this {self.current_task} loan application against bank policy.",
            "is_done": self.is_done
        }
