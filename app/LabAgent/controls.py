import boto3

from config import AWS_REGION, GUARDRAIL_ID, GUARDRAIL_VERSION, PII_SCORE_THRESHOLD

PARTNER_FIELDS = (
    "booking_id",
    "pickup_address",
    "pickup_window",
    "contact_phone",
    "bike_description",
    "bike_notes",
)

# Allow-listed fields 
PARTNER_FREE_TEXT = ("pickup_window", "bike_notes")
WITHHELD = "[withheld: failed outbound check]"

STORAGE_METADATA_KEYS = {"ts", "event", "session_id", "booking_id", "ticket_id"}


class ControlUnavailable(Exception):
    """Raised when an outbound check cannot run."""


_bedrock = None
_comprehend = None


def _bedrock_client():
    global _bedrock
    if _bedrock is None:
        _bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    return _bedrock


def _comprehend_client():
    global _comprehend
    if _comprehend is None:
        _comprehend = boto3.client("comprehend", region_name=AWS_REGION)
    return _comprehend


def for_partner(ticket: dict) -> dict:
    
    payload = {key: ticket[key] for key in PARTNER_FIELDS if key in ticket}

    for key in PARTNER_FREE_TEXT:
        text = payload.get(key)
        if not text:
            continue
        try:
            response = _bedrock_client().apply_guardrail(
                guardrailIdentifier=GUARDRAIL_ID,
                guardrailVersion=GUARDRAIL_VERSION,
                source="OUTPUT",
                content=[{"text": {"text": text}}],
            )
        except Exception as exc:
            raise ControlUnavailable("guardrail check failed") from exc
        if response.get("action") == "GUARDRAIL_INTERVENED":
         #   pass 
           payload[key] = WITHHELD

    return payload


def _redact_text(text: str) -> str:
    response = _comprehend_client().detect_pii_entities(Text=text, LanguageCode="en")
    entities = [e for e in response["Entities"] if e["Score"] >= PII_SCORE_THRESHOLD]
   
    for entity in sorted(entities, key=lambda e: e["BeginOffset"], reverse=True):
        text = text[: entity["BeginOffset"]] + f"[{entity['Type']}]" + text[entity["EndOffset"]:]
    return text


def _redact(value):
    if isinstance(value, str):
        return _redact_text(value) if value.strip() else value
    if isinstance(value, dict):
        return {k: (v if k in STORAGE_METADATA_KEYS else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def for_storage(record: dict) -> dict:
    
    try:
        return _redact(record)
    except Exception:
        kept = {k: v for k, v in record.items() if k in STORAGE_METADATA_KEYS}
        kept["redaction"] = "unavailable, content dropped"
        return kept