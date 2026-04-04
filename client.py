import requests
from typing import Dict, Any

class LoanRiskClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def health(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def reset(self, task: str) -> Dict[str, Any]:
        response = requests.post(f"{self.base_url}/reset", json={"task": task})
        response.raise_for_status()
        return response.json()

    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(f"{self.base_url}/step", json=action)
        response.raise_for_status()
        return response.json()

    def get_state(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/state")
        response.raise_for_status()
        return response.json()
