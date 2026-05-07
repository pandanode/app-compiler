import os

files = {

"pipeline/__init__.py": "",

"schemas/__init__.py": "",

"schemas/intent_schema.py": '''from pydantic import BaseModel, Field
from typing import List

class Entity(BaseModel):
    name: str = Field(..., description="Entity name e.g. User, Product")
    fields: List[str] = Field(..., description="List of field names")

class IntentOutput(BaseModel):
    app_name: str
    description: str
    entities: List[Entity]
    roles: List[str]
    features: List[str]
    has_payments: bool
    has_auth: bool
    is_vague: bool = False
    clarification_needed: str = ""
''',

"schemas/design_schema.py": '''from pydantic import BaseModel
from typing import List

class Relationship(BaseModel):
    from_entity: str
    to_entity: str
    type: str

class Flow(BaseModel):
    name: str
    steps: List[str]

class DesignOutput(BaseModel):
    entities: List[str]
    relationships: List[Relationship]
    user_flows: List[Flow]
    premium_features: List[str]
    public_routes: List[str]
    protected_routes: List[str]
''',

"schemas/db_schema.py": '''from pydantic import BaseModel
from typing import List, Optional

class Column(BaseModel):
    name: str
    type: str
    nullable: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None

class Table(BaseModel):
    name: str
    columns: List[Column]

class DBSchema(BaseModel):
    tables: List[Table]
''',

"schemas/api_schema.py": '''from pydantic import BaseModel
from typing import List

class APIField(BaseModel):
    name: str
    type: str
    required: bool = True

class Endpoint(BaseModel):
    path: str
    method: str
    auth_required: bool
    roles_allowed: List[str]
    request_fields: List[APIField]
    response_fields: List[APIField]

class APISchema(BaseModel):
    base_url: str = "/api"
    endpoints: List[Endpoint]
''',

"schemas/ui_schema.py": '''from pydantic import BaseModel
from typing import List, Optional

class UIComponent(BaseModel):
    type: str
    label: str
    api_endpoint: Optional[str] = None

class Page(BaseModel):
    name: str
    route: str
    auth_required: bool
    roles_allowed: List[str]
    components: List[UIComponent]

class UISchema(BaseModel):
    pages: List[Page]
''',

"schemas/auth_schema.py": '''from pydantic import BaseModel
from typing import List

class Permission(BaseModel):
    role: str
    resource: str
    actions: List[str]

class AuthSchema(BaseModel):
    auth_type: str = "JWT"
    roles: List[str]
    permissions: List[Permission]
    session_expiry_hours: int = 24
''',

"pipeline/repair.py": '''import google.generativeai as genai
import json
import os
from pydantic import BaseModel
from typing import Type, TypeVar
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 0.3,
        "top_p": 0.95,
        "max_output_tokens": 2000,
    }
)

T = TypeVar("T", bound=BaseModel)

def call_llm(system_prompt: str, user_message: str, max_tokens: int = 2000) -> str:
    full_prompt = f"{system_prompt}\\n\\n---\\n\\nUser input:\\n{user_message}"
    response = model.generate_content(full_prompt)
    return response.text.strip()

def parse_json_safe(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\\n".join(lines).strip()
    return json.loads(cleaned)

def validate_and_repair(
    raw_output: str,
    model_class: Type[T],
    original_system: str,
    original_user: str,
    max_retries: int = 3
) -> tuple:
    retries = 0
    for attempt in range(max_retries):
        try:
            data = parse_json_safe(raw_output)
            validated = model_class(**data)
            return validated, retries
        except json.JSONDecodeError as e:
            retries += 1
            print(f"  [Repair] JSON error attempt {attempt+1}: {e}")
            raw_output = call_llm(
                original_system,
                f"Fix this JSON parse error: {e}\\n\\nBad output:\\n{raw_output}\\n\\nReturn ONLY valid JSON. No markdown."
            )
        except Exception as e:
            retries += 1
            print(f"  [Repair] Schema error attempt {attempt+1}: {e}")
            raw_output = call_llm(
                original_system,
                f"Fix this validation error: {e}\\n\\nBad output:\\n{raw_output}\\n\\nReturn corrected JSON only. No markdown."
            )
    raise ValueError(f"Failed after {max_retries} repair attempts. Last: {raw_output}")
''',

"pipeline/stage1_intent.py": '''from pipeline.repair import call_llm, validate_and_repair
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
''',

"pipeline/stage2_design.py": '''import json
from pipeline.repair import call_llm, validate_and_repair
from schemas.intent_schema import IntentOutput
from schemas.design_schema import DesignOutput

SYSTEM = """You are a senior software architect. Given structured app intent, produce a system design.

Return ONLY this JSON, no markdown, no explanation:
{
  "entities": ["User", "Product"],
  "relationships": [{"from_entity": "User", "to_entity": "Order", "type": "one_to_many"}],
  "user_flows": [{"name": "Login Flow", "steps": ["Enter email", "Enter password", "Redirect to dashboard"]}],
  "premium_features": ["analytics"],
  "public_routes": ["/login", "/register"],
  "protected_routes": ["/dashboard"]
}"""

def run(intent: IntentOutput) -> DesignOutput:
    print("[Stage 2] Generating system design...")
    msg = json.dumps(intent.model_dump(), indent=2)
    raw = call_llm(SYSTEM, msg)
    result, retries = validate_and_repair(raw, DesignOutput, SYSTEM, msg)
    print(f"  Done (retries: {retries})")
    return result
''',

"pipeline/stage3_schemas.py": '''import json
from pipeline.repair import call_llm, validate_and_repair
from schemas.intent_schema import IntentOutput
from schemas.design_schema import DesignOutput
from schemas.db_schema import DBSchema
from schemas.api_schema import APISchema
from schemas.ui_schema import UISchema
from schemas.auth_schema import AuthSchema

DB_SYS = """Generate a database schema. Return ONLY JSON, no markdown:
{
  "tables": [
    {
      "name": "users",
      "columns": [
        {"name": "id", "type": "integer", "nullable": false, "primary_key": true, "foreign_key": null},
        {"name": "email", "type": "string", "nullable": false, "primary_key": false, "foreign_key": null}
      ]
    }
  ]
}
Types allowed: string, integer, boolean, datetime, float."""

API_SYS = """Generate an API schema. Return ONLY JSON, no markdown:
{
  "base_url": "/api",
  "endpoints": [
    {
      "path": "/api/users",
      "method": "GET",
      "auth_required": true,
      "roles_allowed": ["admin"],
      "request_fields": [],
      "response_fields": [{"name": "id", "type": "integer", "required": true}]
    }
  ]
}
Methods allowed: GET POST PUT DELETE."""

UI_SYS = """Generate a UI schema. Return ONLY JSON, no markdown:
{
  "pages": [
    {
      "name": "Dashboard",
      "route": "/dashboard",
      "auth_required": true,
      "roles_allowed": ["admin", "user"],
      "components": [
        {"type": "table", "label": "Users List", "api_endpoint": "/api/users"}
      ]
    }
  ]
}
Component types allowed: form, table, chart, card, button."""

AUTH_SYS = """Generate an auth schema. Return ONLY JSON, no markdown:
{
  "auth_type": "JWT",
  "roles": ["admin", "user"],
  "permissions": [
    {"role": "admin", "resource": "users", "actions": ["read", "write", "delete"]}
  ],
  "session_expiry_hours": 24
}"""

def run(intent: IntentOutput, design: DesignOutput) -> dict:
    print("[Stage 3] Generating all schemas...")
    ctx = json.dumps({"intent": intent.model_dump(), "design": design.model_dump()}, indent=2)

    print("  -> DB schema...")
    db, r1 = validate_and_repair(call_llm(DB_SYS, ctx), DBSchema, DB_SYS, ctx)

    print("  -> API schema...")
    api, r2 = validate_and_repair(call_llm(API_SYS, ctx), APISchema, API_SYS, ctx)

    print("  -> UI schema...")
    ui, r3 = validate_and_repair(call_llm(UI_SYS, ctx), UISchema, UI_SYS, ctx)

    print("  -> Auth schema...")
    auth, r4 = validate_and_repair(call_llm(AUTH_SYS, ctx), AuthSchema, AUTH_SYS, ctx)

    print(f"  Done (total retries: {r1+r2+r3+r4})")
    return {"db": db, "api": api, "ui": ui, "auth": auth, "_retries": r1+r2+r3+r4}
''',

"pipeline/stage4_validate.py": '''from schemas.db_schema import DBSchema
from schemas.api_schema import APISchema
from schemas.ui_schema import UISchema
from schemas.auth_schema import AuthSchema

def run(db: DBSchema, api: APISchema, ui: UISchema, auth: AuthSchema) -> dict:
    print("[Stage 4] Running cross-layer validation...")
    errors = []
    warnings = []

    auth_roles = set(auth.roles)

    for ep in api.endpoints:
        for role in ep.roles_allowed:
            if role not in auth_roles:
                errors.append(f"API endpoint \'{ep.path}\' references undefined role \'{role}\'")

    api_paths = {ep.path for ep in api.endpoints}
    for page in ui.pages:
        for comp in page.components:
            if comp.api_endpoint and comp.api_endpoint not in api_paths:
                warnings.append(f"UI \'{comp.label}\' on page \'{page.name}\' calls unknown endpoint \'{comp.api_endpoint}\'")

    for page in ui.pages:
        for role in page.roles_allowed:
            if role not in auth_roles:
                errors.append(f"UI page \'{page.name}\' references undefined role \'{role}\'")

    table_names = {t.name.lower() for t in db.tables}
    if "users" not in table_names and "user" not in table_names:
        warnings.append("No users table in DB schema")

    db_columns = {}
    for table in db.tables:
        db_columns[table.name.lower()] = {col.name.lower() for col in table.columns}

    for ep in api.endpoints:
        path_parts = ep.path.strip("/").split("/")
        if len(path_parts) >= 2:
            resource = path_parts[1].lower().rstrip("s")
            matching_table = None
            for tname in db_columns:
                if resource in tname or tname in resource:
                    matching_table = tname
                    break
            if matching_table:
                for field in ep.response_fields:
                    if field.name.lower() not in db_columns[matching_table]:
                        warnings.append(f"API \'{ep.path}\' returns field \'{field.name}\' not in DB table \'{matching_table}\'")

    status = "PASS" if not errors else "FAIL"
    print(f"  Validation: {status} | {len(errors)} errors, {len(warnings)} warnings")
    return {"status": status, "errors": errors, "warnings": warnings}
''',

"main.py": '''import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pipeline import stage1_intent, stage2_design, stage3_schemas, stage4_validate

app = FastAPI(title="App Compiler")
app.mount("/static", StaticFiles(directory="frontend"), name="static")

class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
def serve_ui():
    return FileResponse("frontend/index.html")

@app.post("/compile")
def compile_app(req: PromptRequest):
    try:
        intent  = stage1_intent.run(req.prompt)
        design  = stage2_design.run(intent)
        schemas = stage3_schemas.run(intent, design)
        val     = stage4_validate.run(
            schemas["db"], schemas["api"], schemas["ui"], schemas["auth"]
        )
        return {
            "status": "success",
            "intent":      intent.model_dump(),
            "design":      design.model_dump(),
            "db_schema":   schemas["db"].model_dump(),
            "api_schema":  schemas["api"].model_dump(),
            "ui_schema":   schemas["ui"].model_dump(),
            "auth_schema": schemas["auth"].model_dump(),
            "validation":  val,
            "retries":     schemas["_retries"]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
''',

"test_gemini.py": '''from pipeline.repair import call_llm

result = call_llm(
    system_prompt="You are a helpful assistant. Return only valid JSON.",
    user_message=\'Return this exact JSON: {"status": "working", "model": "gemini"}\'
)
print("Gemini response:")
print(result)
''',

"evaluation/test_prompts.py": '''REAL_PROMPTS = [
    "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments.",
    "Create an e-commerce platform with product listings, cart, checkout, and admin panel.",
    "Build a project management tool like Trello with boards, cards, teams, and notifications.",
    "Create a booking system for a clinic with doctors, patients, appointments, and billing.",
    "Build a SaaS analytics dashboard with multi-tenant support, charts, and API access.",
    "Create a food delivery app with restaurants, menus, orders, drivers, and tracking.",
    "Build a learning management system with courses, students, quizzes, and certificates.",
    "Create a HR platform with employees, payroll, leave management, and org chart.",
    "Build a real estate platform with listings, agents, bookings, and mortgage calculator.",
    "Create a social media app with posts, follows, likes, comments, and notifications.",
]

EDGE_CASES = [
    "Build an app.",
    "Make something for my business.",
    "Build a system with login but also without login.",
    "Create a free app but charge users for everything.",
    "Build a platform.",
    "App with users.",
    "Build what base44 built but better.",
    "CRM + ERP + HRM + CMS + LMS all in one.",
    "Build an app that works offline and syncs in real-time.",
    "Create an AI-powered app that does everything automatically.",
]
''',

"evaluation/eval_runner.py": '''import time
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import stage1_intent, stage2_design, stage3_schemas, stage4_validate
from evaluation.test_prompts import REAL_PROMPTS, EDGE_CASES

def run_single(prompt: str) -> dict:
    start = time.time()
    try:
        intent  = stage1_intent.run(prompt)
        design  = stage2_design.run(intent)
        schemas = stage3_schemas.run(intent, design)
        val     = stage4_validate.run(schemas["db"], schemas["api"], schemas["ui"], schemas["auth"])
        return {
            "status": "success",
            "latency_s": round(time.time() - start, 2),
            "retries": schemas["_retries"],
            "validation": val["status"],
            "is_vague": intent.is_vague
        }
    except Exception as e:
        return {"status": "error", "latency_s": round(time.time() - start, 2), "error": str(e)}

def run_eval():
    results = {"real": [], "edge": []}

    print("\\n=== REAL PROMPTS ===")
    for p in REAL_PROMPTS:
        print(f"\\nPrompt: {p[:60]}...")
        r = run_single(p)
        results["real"].append(r)
        print(f"  Result: {r[\'status\']} | {r.get(\'latency_s\')}s | retries: {r.get(\'retries\', 0)}")

    print("\\n=== EDGE CASES ===")
    for p in EDGE_CASES:
        print(f"\\nPrompt: {p[:60]}...")
        r = run_single(p)
        results["edge"].append(r)
        print(f"  Result: {r[\'status\']} | {r.get(\'latency_s\')}s")

    real_success = sum(1 for r in results["real"] if r["status"] == "success")
    edge_success = sum(1 for r in results["edge"] if r["status"] == "success")
    avg_latency  = sum(r["latency_s"] for r in results["real"]) / len(results["real"])
    avg_retries  = sum(r.get("retries", 0) for r in results["real"]) / len(results["real"])

    print(f"""
=== METRICS ===
Real prompts:  {real_success}/10 success ({real_success*10}%)
Edge cases:    {edge_success}/10 handled ({edge_success*10}%)
Avg latency:   {round(avg_latency, 2)}s
Avg retries:   {round(avg_retries, 2)}
""")

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to eval_results.json")

if __name__ == "__main__":
    run_eval()
''',

"frontend/index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>App Compiler</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: monospace; background: #0f0f0f; color: #e0e0e0; padding: 32px; }
  h1 { color: #a78bfa; margin-bottom: 8px; font-size: 24px; }
  p  { color: #888; margin-bottom: 24px; font-size: 14px; }
  textarea { width: 100%; height: 100px; background: #1a1a1a; border: 1px solid #333;
             color: #e0e0e0; padding: 12px; font-size: 14px; border-radius: 6px; resize: vertical; }
  button { margin-top: 12px; padding: 10px 28px; background: #7c3aed; color: white;
           border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
  button:hover { background: #6d28d9; }
  #status { margin-top: 16px; font-size: 13px; color: #888; min-height: 20px; }
  #output { margin-top: 16px; background: #1a1a1a; border: 1px solid #333;
            padding: 16px; border-radius: 6px; white-space: pre-wrap;
            font-size: 12px; max-height: 600px; overflow-y: auto; display: none; }
</style>
</head>
<body>
  <h1>App Compiler</h1>
  <p>Natural language to validated app schema — 4-stage pipeline</p>
  <textarea id="prompt" placeholder="Build a CRM with login, contacts, dashboard, role-based access and payments..."></textarea>
  <br>
  <button onclick="compile()">Compile</button>
  <div id="status"></div>
  <pre id="output"></pre>
  <script>
    async function compile() {
      const prompt = document.getElementById("prompt").value.trim();
      if (!prompt) return;
      document.getElementById("status").textContent = "Running pipeline...";
      document.getElementById("output").style.display = "none";
      try {
        const res = await fetch("/compile", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt })
        });
        const data = await res.json();
        document.getElementById("status").textContent =
          data.status === "success"
            ? "Done — validation: " + data.validation?.status + " | retries: " + data.retries
            : "Error: " + data.message;
        document.getElementById("output").style.display = "block";
        document.getElementById("output").textContent = JSON.stringify(data, null, 2);
      } catch (e) {
        document.getElementById("status").textContent = "Network error: " + e.message;
      }
    }
  </script>
</body>
</html>
''',

"requirements.txt": '''google-generativeai
pydantic
fastapi
uvicorn
python-dotenv
'''

}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Written: {filepath}")

print("\nAll files written successfully!")
print("Next step: python test_gemini.py")