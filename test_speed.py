import requests, os, time
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = [
    "openai/gpt-oss-20b:free",
    "openai/gpt-oss-120b:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "poolside/laguna-xs.2:free",
    "poolside/laguna-m.1:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "z-ai/glm-4.5-air:free",
    "qwen/qwen3-coder:free",
]

PROMPT = """Return ONLY valid JSON, no markdown, no explanation:
{"tables": [{"name": "users", "columns": [{"name": "id", "type": "integer", "nullable": false, "primary_key": true, "foreign_key": null}, {"name": "email", "type": "string", "nullable": false, "primary_key": false, "foreign_key": null}]}]}"""

results = []
for model in MODELS:
    try:
        t = time.time()
        r = requests.post(URL, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": model,
            "max_tokens": 300,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": PROMPT}]
        }, timeout=30)
        elapsed = round(time.time() - t, 2)
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"].strip()[:80]
            print(f"WORKS {elapsed}s -- {model}")
            print(f"  Preview: {content}")
            results.append((elapsed, model))
        else:
            print(f"FAIL {r.status_code} -- {model}")
    except Exception as e:
        print(f"TIMEOUT -- {model}")

if results:
    results.sort()
    print(f"\n--- RANKING ---")
    for t, m in results:
        print(f"  {t}s -- {m}")
    print(f"\nWINNER: MODEL = \"{results[0][1]}\"")