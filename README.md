# PiiLab: Ridgeline Moto service desk agent

An AgentCore agent for a motorcycle repair shop. Customers can check on a bike's
service status and book a pickup with an outside transport service.

## Setup

    python -m venv .venv
    source .venv/bin/activate        
    Windows: source .venv/Scripts/activate
    pip install -r requirements.txt

## Tests



    pytest

Tests replace Comprehend and the guardrail with local fakes, so they need no AWS
credentials.

## Run the agent

Copy `.env.example` to `app/LabAgent/.env` and fill in:

    AWS_REGION=
    BEDROCK_MODEL_ID=
    BEDROCK_MAX_TOKENS=
    GUARDRAIL_ID=
    GUARDRAIL_VERSION=

The AWS identity running the agent needs 
1. `bedrock:InvokeModel`,
2. `bedrock:ApplyGuardrail` 
3. `comprehend:DetectPiiEntities`.

From the repo root:

    agentcore dev

In a second terminal:

    agentcore invoke --dev "What's the status on ticket RT-2207?"

## Output files

- `logs/audit.jsonl`: audit log, redacted at write time
- `outbox/transport.jsonl`: what the simulated transport service received

Both are gitignored. To check nothing leaked:

    grep -rn "alex.testrider@example.com" --include="*.jsonl" .