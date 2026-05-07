import json
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
