from pipeline import stage1_intent, stage2_design, stage3_schemas, stage4_validate
import json

prompt = "Build a CRM with login, contacts, dashboard, role-based access, and payments."

intent  = stage1_intent.run(prompt)
design  = stage2_design.run(intent)
schemas = stage3_schemas.run(intent, design)
val     = stage4_validate.run(
    schemas["db"], schemas["api"], schemas["ui"], schemas["auth"]
)

print("\n=== FINAL OUTPUT ===")
print(json.dumps({
    "intent":     intent.model_dump(),
    "design":     design.model_dump(),
    "validation": val
}, indent=2))