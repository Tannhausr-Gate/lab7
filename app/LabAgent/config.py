import os

from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.environ["AWS_REGION"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
BEDROCK_MAX_TOKENS = int(os.environ["BEDROCK_MAX_TOKENS"])
GUARDRAIL_ID = os.environ["GUARDRAIL_ID"]
GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "DRAFT")
PII_SCORE_THRESHOLD = float(os.environ.get("PII_SCORE_THRESHOLD", "0.5"))
AUDIT_LOG_PATH = os.environ.get("AUDIT_LOG_PATH", "logs/audit.jsonl")
PARTNER_OUTBOX_PATH = os.environ.get("PARTNER_OUTBOX_PATH", "outbox/transport.jsonl")