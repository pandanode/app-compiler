from schemas.db_schema import DBSchema
from schemas.api_schema import APISchema
from schemas.ui_schema import UISchema
from schemas.auth_schema import AuthSchema

def run(db: DBSchema, api: APISchema, ui: UISchema, auth: AuthSchema) -> dict:
    print("[Stage 4] Running cross-layer validation...")
    errors = []
    warnings = []

    IGNORED_RESPONSE_FIELDS = {
    "message", "token", "success", "status", "updated", "deleted",
    "payment_id", "created_at", "updated_at", "access_token",
    "refresh_token", "expires_in", "total", "count", "page",
    "next", "previous", "results", "data", "meta", "error",
    "owner_id", "user_id", "author_id", "slug", "thumbnail",
    "avatar", "image_url", "is_active", "is_verified", "role"
}

    AUTH_ENDPOINTS = {
        "/api/auth/login", "/api/auth/logout", "/api/auth/register",
        "/api/auth/refresh", "/api/auth/me"
    }

    auth_roles = set(auth.roles)

    for ep in api.endpoints:
        for role in ep.roles_allowed:
            if role not in auth_roles:
                errors.append(f"API endpoint '{ep.path}' references undefined role '{role}'")

    api_paths = {ep.path for ep in api.endpoints}
    for page in ui.pages:
        for comp in page.components:
            if comp.api_endpoint and comp.api_endpoint not in api_paths:
                if comp.api_endpoint not in AUTH_ENDPOINTS:
                    warnings.append(f"UI '{comp.label}' on page '{page.name}' calls unknown endpoint '{comp.api_endpoint}'")

    for page in ui.pages:
        for role in page.roles_allowed:
            if role not in auth_roles:
                errors.append(f"UI page '{page.name}' references undefined role '{role}'")

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
                        if field.name.lower() not in IGNORED_RESPONSE_FIELDS:
                            warnings.append(f"API '{ep.path}' returns field '{field.name}' not in DB table '{matching_table}'")

    status = "PASS" if not errors else "FAIL"
    print(f"  Validation: {status} | {len(errors)} errors, {len(warnings)} warnings")
    return {"status": status, "errors": errors, "warnings": warnings}