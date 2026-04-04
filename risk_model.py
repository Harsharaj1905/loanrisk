"""
LoanRisk Neural Network - PyTorch Risk Scorer
A feedforward neural network that predicts loan risk probability
from applicant features. Used to pre-screen cases before LLM reasoning.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, Any, Tuple

# ── Feature Engineering ────────────────────────────────────────────────────────

def extract_features(profile: Dict[str, Any], policy: Dict[str, Any]) -> torch.Tensor:
    """
    Convert raw applicant profile + bank policy into a normalized
    feature vector for the neural network.

    Features (10 total):
      0  credit_score_ratio     credit_score / min_credit_score
      1  debt_ratio_ratio       debt_ratio / max_debt_ratio
      2  ltv_ratio              loan_amount / property_value
      3  ltv_policy_ratio       ltv / max_ltv
      4  employment_years_ratio years_employed / min_years_employed
      5  income_normalized      income / 200000 (clipped)
      6  has_co_applicant       0 or 1
      7  is_self_employed       0 or 1
      8  has_missing_data       1 if credit/debt/income is None
      9  is_investment          1 if purpose == investment
    """
    credit = profile.get("credit_score") or 0
    debt_ratio = profile.get("debt_ratio") or 0
    loan = profile.get("loan_amount") or 0
    value = profile.get("property_value") or 1
    years = profile.get("years_employed") or 0
    income = profile.get("income") or 0
    has_co = float(profile.get("has_co_applicant", False))
    emp_type = profile.get("employment_type", "")
    purpose = profile.get("purpose", "")

    min_credit = policy.get("min_credit_score", 650)
    max_debt = policy.get("max_debt_ratio", 0.43)
    min_years = policy.get("min_years_employed", 2)
    max_ltv = policy.get("max_ltv", 0.80)

    ltv = loan / value if value else 1.0

    has_missing = float(
        profile.get("credit_score") is None or
        profile.get("debt_ratio") is None or
        profile.get("income") is None
    )

    features = [
        min(credit / max(min_credit, 1), 2.0),          # 0 credit ratio (>1 = good)
        min(debt_ratio / max(max_debt, 0.01), 2.0),      # 1 debt ratio (>1 = bad)
        min(ltv, 1.5),                                    # 2 LTV
        min(ltv / max(max_ltv, 0.01), 2.0),              # 3 LTV vs policy
        min(years / max(min_years, 1), 3.0),              # 4 employment ratio
        min(income / 200000.0, 2.0),                      # 5 income normalized
        has_co,                                           # 6 co-applicant flag
        float("self_employed" in emp_type),               # 7 self-employed flag
        has_missing,                                      # 8 missing data flag
        float(purpose == "investment"),                   # 9 investment flag
    ]

    return torch.tensor(features, dtype=torch.float32)


# ── Model Architecture ─────────────────────────────────────────────────────────

class LoanRiskNet(nn.Module):
    """
    Feedforward neural network for loan risk scoring.
    Input:  10 normalized features
    Output: risk probability in [0, 1]
             0.0 = very low risk (approve)
             1.0 = very high risk (reject)
    """
    def __init__(self, input_dim: int = 10, hidden_dim: int = 32):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x).squeeze(-1)


# ── Training Data ──────────────────────────────────────────────────────────────

# (profile, policy, risk_label) where label: 0=low, 0.5=medium, 1=high
TRAINING_DATA = [
    # Easy approvals → low risk
    ({"credit_score": 780, "income": 95000, "debt_ratio": 0.18,
      "loan_amount": 200000, "property_value": 400000, "years_employed": 6,
      "has_co_applicant": False, "employment_type": "salaried", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     0.0),

    ({"credit_score": 810, "income": 120000, "debt_ratio": 0.25,
      "loan_amount": 300000, "property_value": 600000, "years_employed": 10,
      "has_co_applicant": False, "employment_type": "salaried", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     0.0),

    # Clear rejections → high risk
    ({"credit_score": 520, "income": 42000, "debt_ratio": 0.55,
      "loan_amount": 180000, "property_value": 220000, "years_employed": 3,
      "has_co_applicant": False, "employment_type": "salaried", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     1.0),

    ({"credit_score": 600, "income": 55000, "debt_ratio": 0.38,
      "loan_amount": 140000, "property_value": 200000, "years_employed": 1,
      "has_co_applicant": False, "employment_type": "salaried", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     1.0),

    ({"credit_score": 590, "income": 62000, "debt_ratio": None,
      "loan_amount": 190000, "property_value": 230000, "years_employed": 1,
      "has_co_applicant": False, "employment_type": "contract", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     1.0),

    # Borderline / medium risk
    ({"credit_score": 630, "income": 78000, "debt_ratio": 0.41,
      "loan_amount": 250000, "property_value": 350000, "years_employed": 3,
      "has_co_applicant": True, "employment_type": "salaried", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2,
      "max_ltv": 0.80, "co_applicant_exception": True},
     0.5),

    ({"credit_score": 640, "income": 92000, "debt_ratio": 0.28,
      "loan_amount": 200000, "property_value": 380000, "years_employed": 3,
      "has_co_applicant": False, "employment_type": "self_employed", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     0.5),

    ({"credit_score": 720, "income": 48000, "debt_ratio": 0.45,
      "loan_amount": 160000, "property_value": 220000, "years_employed": 5,
      "has_co_applicant": False, "employment_type": "salaried", "purpose": "refinance"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     0.8),

    # Hard cases
    ({"credit_score": 660, "income": 75000, "debt_ratio": 0.48,
      "loan_amount": 310000, "property_value": 400000, "years_employed": 5,
      "has_co_applicant": True, "employment_type": "salaried", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2,
      "max_ltv": 0.80, "co_applicant_exception": True},
     0.9),

    ({"credit_score": 670, "income": 88000, "debt_ratio": 0.37,
      "loan_amount": 240000, "property_value": 320000, "years_employed": 1,
      "has_co_applicant": False, "employment_type": "self_employed", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     0.8),

    ({"credit_score": 645, "income": 130000, "debt_ratio": 0.42,
      "loan_amount": 500000, "property_value": 620000, "years_employed": 7,
      "has_co_applicant": True, "employment_type": "salaried", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2,
      "max_ltv": 0.80, "co_applicant_exception": True, "jumbo_loan_threshold": 450000},
     0.5),

    # Synthetic augmented cases
    ({"credit_score": 750, "income": 85000, "debt_ratio": 0.30,
      "loan_amount": 220000, "property_value": 400000, "years_employed": 8,
      "has_co_applicant": False, "employment_type": "salaried", "purpose": "home_purchase"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     0.1),

    ({"credit_score": 580, "income": 35000, "debt_ratio": 0.60,
      "loan_amount": 200000, "property_value": 210000, "years_employed": 0,
      "has_co_applicant": False, "employment_type": "contract", "purpose": "investment"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     1.0),

    ({"credit_score": 700, "income": 95000, "debt_ratio": 0.35,
      "loan_amount": 280000, "property_value": 400000, "years_employed": 5,
      "has_co_applicant": False, "employment_type": "salaried", "purpose": "refinance"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2, "max_ltv": 0.80},
     0.2),

    ({"credit_score": 610, "income": None, "debt_ratio": 0.39,
      "loan_amount": 280000, "property_value": 360000, "years_employed": 4,
      "has_co_applicant": True, "employment_type": "self_employed", "purpose": "investment"},
     {"min_credit_score": 650, "max_debt_ratio": 0.43, "min_years_employed": 2,
      "max_ltv": 0.80, "co_applicant_exception": True},
     0.85),
]


# ── Training ───────────────────────────────────────────────────────────────────

def train_model(epochs: int = 300, lr: float = 0.005) -> LoanRiskNet:
    """Train the PyTorch model on loan data."""
    model = LoanRiskNet()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.MSELoss()

    # Build tensors
    X = torch.stack([extract_features(p, pol) for p, pol, _ in TRAINING_DATA])
    y = torch.tensor([label for _, _, label in TRAINING_DATA], dtype=torch.float32)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        preds = model(X)
        loss = criterion(preds, y)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 100 == 0:
            print(f"  [PyTorch] Epoch {epoch+1}/{epochs} — Loss: {loss.item():.4f}")

    model.eval()
    return model


# ── Inference ──────────────────────────────────────────────────────────────────

def risk_score(
    model: LoanRiskNet,
    profile: Dict[str, Any],
    policy: Dict[str, Any]
) -> Tuple[float, str]:
    """
    Get risk probability and label from the neural network.
    Returns: (score float 0-1, label str)
    """
    model.eval()
    with torch.no_grad():
        features = extract_features(profile, policy).unsqueeze(0)
        prob = model(features).item()

    if prob < 0.3:
        label = "low"
    elif prob < 0.65:
        label = "medium"
    else:
        label = "high"

    return round(prob, 3), label


# ── Singleton model (trained once on import) ───────────────────────────────────

print("[PyTorch] Training LoanRiskNet...")
_MODEL = train_model(epochs=300)
print("[PyTorch] Model ready.")


def get_risk_score(profile: Dict[str, Any], policy: Dict[str, Any]) -> Tuple[float, str]:
    """Public API — returns (risk_probability, risk_label)."""
    return risk_score(_MODEL, profile, policy)
