import requests, os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

r = requests.get("https://openrouter.ai/api/v1/models", headers={
    "Authorization": f"Bearer {API_KEY}"
})

models = r.json()["data"]
free_models = [m for m in models if ":free" in m["id"]]

print(f"Total free models: {len(free_models)}\n")
for m in sorted(free_models, key=lambda x: x["id"]):
    print(m["id"])