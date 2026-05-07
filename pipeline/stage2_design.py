import json
from pipeline.repair import call_llm, validate_and_repair
from schemas.intent_schema import IntentOutput
from schemas.design_schema import DesignOutput

SYSTEM = """You are a senior software architect. Given structured app intent, produce a system design.

CRITICAL: Return ONLY a raw JSON object. No questions. No explanations. No markdown. No backticks.
If anything is unclear, make reasonable assumptions and proceed.

You MUST return exactly this structure:
{
  "entities": ["User", "Contact", "Payment"],
  "relationships": [
    {"from_entity": "User", "to_entity": "Contact", "type": "one_to_many"}
  ],
  "user_flows": [
    {"name": "Login Flow", "steps": ["Enter email", "Enter password", "Redirect to dashboard"]}
  ],
  "premium_features": ["advanced analytics", "bulk export"],
  "public_routes": ["/login", "/register"],
  "protected_routes": ["/dashboard", "/contacts", "/admin"]
}"""

def run(intent: IntentOutput) -> DesignOutput:
    print("[Stage 2] Generating system design...")
    msg = json.dumps(intent.model_dump(), indent=2)
    raw = call_llm(SYSTEM, msg)
    result, retries = validate_and_repair(raw, DesignOutput, SYSTEM, msg)
    print(f"  Done (retries: {retries})")
    return result
