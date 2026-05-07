import requests
import json
import os
from pydantic import BaseModel
from typing import Type, TypeVar
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
PRIMARY_MODEL = "openai/gpt-oss-120b:free"
FALLBACK_MODEL = "openai/gpt-oss-120b:free"

T = TypeVar("T", bound=BaseModel)


def call_llm(system_prompt: str, user_message: str, max_tokens: int = 700, use_fallback: bool = False) -> str:
    model = FALLBACK_MODEL if use_fallback else PRIMARY_MODEL
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "App Compiler"
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ]
    }
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    if content is None:
        raise ValueError(f"Model {model} returned null content")
    return content.strip()

def parse_json_safe(raw: str) -> dict:
    """
    Robustly extract JSON from LLM output.
    Handles: markdown fences, extra text after JSON, nested objects.
    """
    cleaned = raw.strip()

    # Remove markdown fences
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    # Extract just the JSON object — find first { and its matching }
    start = cleaned.find("{")
    if start == -1:
        raise json.JSONDecodeError("No JSON object found", cleaned, 0)

    # Find the matching closing brace
    depth = 0
    end = -1
    for i, ch in enumerate(cleaned[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end == -1:
        raise json.JSONDecodeError("Unclosed JSON object", cleaned, start)

    json_str = cleaned[start:end]
    return json.loads(json_str)


def fix_common_errors(data: dict, model_class: Type) -> dict:
    """
    Fix known structural mistakes before Pydantic validation.
    """
    # Fix DB schema issues
    if "tables" in data:
        for table in data["tables"]:
            # Fix: 'fields' used instead of 'columns'
            if "fields" in table and "columns" not in table:
                table["columns"] = table.pop("fields")

            if "columns" in table:
                fixed_cols = []
                for col in table["columns"]:
                    # Fix: foreign_key as dict instead of string
                    fk = col.get("foreign_key", None)
                    if isinstance(fk, dict):
                        # Convert {"table": "users", "column": "id"} → "users.id"
                        fk = f"{fk.get('table', '')}.{fk.get('column', 'id')}"
                    elif fk == "" or fk == "null":
                        fk = None

                    fixed_col = {
                        "name": col.get("name", "id"),
                        "type": col.get("type", "string"),
                        "nullable": col.get("nullable", False),
                        "primary_key": col.get("primary_key", False),
                        "foreign_key": fk
                    }
                    fixed_cols.append(fixed_col)
                table["columns"] = fixed_cols

    return data


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
            data = fix_common_errors(data, model_class)
            validated = model_class(**data)
            return validated, retries
        except json.JSONDecodeError as e:
            retries += 1
            print(f"  [Repair] JSON error attempt {attempt+1}: {e}")
            raw_output = call_llm(
                original_system,
                f"Fix this JSON parse error: {e}\n\nBad output:\n{raw_output}\n\nReturn ONLY valid JSON. No markdown. No extra text.",
                use_fallback=True   # ← always use strong model for repairs
            )
        except Exception as e:
            retries += 1
            print(f"  [Repair] Schema error attempt {attempt+1}: {e}")
            raw_output = call_llm(
                original_system,
                f"Fix this validation error: {e}\n\nBad output:\n{raw_output}\n\nReturn corrected JSON only. No markdown. No extra text.",
                use_fallback=True
            )
    raise ValueError(f"Failed after {max_retries} attempts. Last output: {raw_output}")