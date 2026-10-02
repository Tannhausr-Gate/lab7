from langchain_aws import ChatBedrockConverse
from config import AWS_REGION, BEDROCK_MODEL_ID

# Uses global inference profile for Claude Sonnet 4.5
# https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html
# MODEL_ID = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"


def load_model() -> ChatBedrockConverse:
    """Get Bedrock model client using IAM credentials."""
    return ChatBedrockConverse(model_id=BEDROCK_MODEL_ID, region_name=AWS_REGION)
