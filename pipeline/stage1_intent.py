from pipeline.repair import call_llm, validate_and_repair
from schemas.intent_schema import IntentOutput

SYSTEM = """You are a senior software architect. Extract structured intent from the user app description.

Return ONLY this JSON structure, no markdown, no explanation:
{
  "app_name": "string",
  "description": "string",
  "entities": [{"name": "string", "fields": ["field1", "field2"]}],
  "roles": ["admin", "user"],
  "features": ["login", "dashboard"],
  "has_payments": true,
  "has_auth": true,
  "is_vague": false,
  "clarification_needed": ""
}"""

def run(user_prompt: str) -> IntentOutput:
    print("[Stage 1] Extracting intent...")
    raw = call_llm(SYSTEM, user_prompt)
    result, retries = validate_and_repair(raw, IntentOutput, SYSTEM, user_prompt)
    print(f"  Done (retries: {retries})")
    return result
