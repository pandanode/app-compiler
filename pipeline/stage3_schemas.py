import json
from pipeline.repair import call_llm, validate_and_repair
from schemas.intent_schema import IntentOutput
from schemas.design_schema import DesignOutput
from schemas.db_schema import DBSchema
from schemas.api_schema import APISchema
from schemas.ui_schema import UISchema
from schemas.auth_schema import AuthSchema

DB_SYS = """You are a database architect. Generate a database schema based on the app context.

CRITICAL: Return ONLY raw JSON. No questions. No explanations. No markdown. No backticks.
Make reasonable assumptions for anything unclear. Always include a users table.

Return exactly this structure:
{
  "tables": [
    {
      "name": "users",
      "columns": [
        {"name": "id", "type": "integer", "nullable": false, "primary_key": true, "foreign_key": null},
        {"name": "email", "type": "string", "nullable": false, "primary_key": false, "foreign_key": null},
        {"name": "role", "type": "string", "nullable": false, "primary_key": false, "foreign_key": null}
      ]
    }
  ]
}
Types allowed: string, integer, boolean, datetime, float."""

API_SYS = """You are a backend architect. Generate a REST API schema based on the app context.

CRITICAL: Return ONLY raw JSON. No questions. No explanations. No markdown. No backticks.
Make reasonable assumptions for anything unclear.
CRITICAL: roles_allowed values MUST only come from the roles list provided in the context. Do NOT invent new roles.

Return exactly this structure:
{
  "base_url": "/api",
  "endpoints": [
    {
      "path": "/api/users",
      "method": "GET",
      "auth_required": true,
      "roles_allowed": ["admin"],
      "request_fields": [],
      "response_fields": [
        {"name": "id", "type": "integer", "required": true},
        {"name": "email", "type": "string", "required": true}
      ]
    }
  ]
}
Methods allowed: GET POST PUT DELETE."""

UI_SYS = """You are a frontend architect. Generate a UI schema based on the app context.

CRITICAL: Return ONLY raw JSON. No questions. No explanations. No markdown. No backticks.
CRITICAL: roles_allowed values MUST only come from the roles list provided in the context. Do NOT invent new roles.
CRITICAL: Every api_endpoint value MUST exactly match one of the API paths provided in the context. Do NOT invent new endpoints.

Return exactly this structure:
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

AUTH_SYS = """You are a security architect. Generate an auth schema based on the app context.

CRITICAL: Return ONLY raw JSON. No questions. No explanations. No markdown. No backticks.
CRITICAL: roles list MUST exactly match the roles provided in the context. Do NOT invent new roles.

Return exactly this structure:
{
  "auth_type": "JWT",
  "roles": ["admin", "user"],
  "permissions": [
    {"role": "admin", "resource": "users", "actions": ["read", "write", "delete"]},
    {"role": "user", "resource": "users", "actions": ["read"]}
  ],
  "session_expiry_hours": 24
}"""


def run(intent: IntentOutput, design: DesignOutput) -> dict:
    print("[Stage 3] Generating all schemas...")

    roles = intent.roles if intent.roles else ["admin", "user"]

    ctx_base = {"intent": intent.model_dump(), "design": design.model_dump()}

    # Inject roles explicitly into context
    ctx_with_roles = json.dumps({
        **ctx_base,
        "REQUIRED_ROLES": roles,
        "instructions": f"You MUST use ONLY these roles: {roles}. Do not use any other role names."
    }, indent=2)

    print("  -> DB schema...")
    db, r1 = validate_and_repair(call_llm(DB_SYS, ctx_with_roles), DBSchema, DB_SYS, ctx_with_roles)

    print("  -> API schema...")
    api, r2 = validate_and_repair(call_llm(API_SYS, ctx_with_roles), APISchema, API_SYS, ctx_with_roles)

    # Build UI context with actual API paths so model can't invent endpoints
    api_paths = [ep.path for ep in api.endpoints]
    ctx_with_api = json.dumps({
        **ctx_base,
        "REQUIRED_ROLES": roles,
        "AVAILABLE_API_PATHS": api_paths,
        "instructions": f"You MUST use ONLY these roles: {roles}. You MUST use ONLY these api_endpoint values: {api_paths}."
    }, indent=2)

    print("  -> UI schema...")
    ui, r3 = validate_and_repair(call_llm(UI_SYS, ctx_with_api), UISchema, UI_SYS, ctx_with_api)

    print("  -> Auth schema...")
    auth, r4 = validate_and_repair(call_llm(AUTH_SYS, ctx_with_roles), AuthSchema, AUTH_SYS, ctx_with_roles)

    print(f"  Done (total retries: {r1+r2+r3+r4})")
    return {"db": db, "api": api, "ui": ui, "auth": auth, "_retries": r1+r2+r3+r4}