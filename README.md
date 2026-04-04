# LoanRisk-OpenEnv (Meta × PyTorch × HF Hackathon Submission)

This is my submission for the April 2026 OpenEnv hackathon. I noticed a lot of RL environments are just simple toy games (like moving a block around a grid), so I wanted to build something grounded in the real world: **Assessing bank loan applications**.

LoanRisk is an OpenEnv-compliant environment where an AI agent acts as a loan officer. It evaluates an applicant's financial profile against bank policies and decides whether to approve, reject, escalate, or request more documents.

## What's actually in here?

I've structured the environment specifically to meet the strict bounds of the OpenEnv spec.

- **`server/`**: Contains the FastAPI backend and the core `environment.py`. This holds the logic for resetting episodes, applying state, and grading the agent's actions (giving partial rewards based on matching specific risk flags, criteria, etc.)
- **`models.py` & `client.py`**: The raw Pydantic schemas (typed strictly for validation) and a simple HTTP wrapper to interface with the local server.
- **`inference.py`**: A complete run-loop for the agent. It tackles 9 episodes (easy, medium, hard). To avoid burning through API tokens and latency, I built a hybrid stack. About 60% of cases are mapped out via a strict rule-based layer first. If it's a weird edge-case that bypasses my direct logic, it falls back to a zero-shot LLM call via the standard OpenAI client.
- **`frontend/`**: I wired up a clean, zero-dependency glassmorphism dashboard served directly out of the FastAPI app so reviewers can manually run grading iterations themselves without reading JSON dumps.

## Getting Started

You'll need a standard Python 3.11+ setup. You don't need a GPU locally since the intensive LLM routing hits the API endpoints anyway.

### 1. Set your environment variables
Make sure you export the required keys so `inference.py` can authenticate:
```bash
export API_BASE_URL="your-endpoint-url"
export MODEL_NAME="gpt-4o"
export HF_TOKEN="your-api-key"
```

### 2. Spinning up the Backend + UI
The easiest way is just to use Docker. I put the `Dockerfile` in the root folder so it builds cleanly without internet access after the initial pip install dependencies block.

```bash
docker build -t loanrisk-env .
docker run -p 7860:7860 loanrisk-env
```

If you prefer running it bare-metal locally:
```bash
pip install -r server/requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

Once running, you can hit **http://localhost:7860/ui** in your browser to play with the manual evaluator dashboard.

### 3. Running the Agent (Inference)
The automated runner expects the backend to be alive on port 7860.
Just run:
```bash
python inference.py
```

It spits out exactly the `[START]`, `[STEP]`, and `[END]` formats mandated by the competition rules to standard output. Reward tracking is logged sequentially, and the final results are dumped into `outputs/evals/inference_results.json`.

## Notes on the Grader

The reward function isn't just binary pass/fail. 
- You get +0.40 for just making the right final call (e.g. Reject vs Escalate).
- Getting the exact risk level correct gets another +0.20.
- Identifying the *exact* failing criteria (e.g. debt ratio too high) gives +0.10 per flag, maxing at 3.
- If the agent hallucinates flags that weren't there, it gets docked points.

I threw in a `# TODO` to eventually add dynamic curriculum weighting so harder cases drop more frequently once the agent consistently clears the easy ones, but that's a problem for post-hackathon refactoring.
