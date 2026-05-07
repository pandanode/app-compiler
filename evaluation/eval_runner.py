import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import stage1_intent, stage2_design, stage3_schemas, stage4_validate

PROMPTS = [
    "Build a CRM with login, contacts, dashboard, role-based access, and payments.",
    "Create a todo app with user accounts and task categories.",
    "Build a blog platform with posts, comments, and admin moderation.",
    "Create an e-commerce store with products, cart, and checkout.",
    "Build a project management tool with tasks, teams, and deadlines.",
    "Create a booking system for a clinic with appointments and doctors.",
    "Build a school management system with students, courses, and grades.",
    "Create a food delivery app with restaurants, menus, and orders.",
    "Build a job board with listings, applications, and employer profiles.",
    "Create a social media app with posts, likes, follows, and messaging.",
]

results = []
passed = 0
total_retries = 0
total_time = 0

print("=" * 60)
print("EVALUATION RUNNER — 10 prompts")
print("=" * 60)

for i, prompt in enumerate(PROMPTS, 1):
    print(f"\n[{i}/10] {prompt[:55]}...")
    t = time.time()
    try:
        intent  = stage1_intent.run(prompt)
        design  = stage2_design.run(intent)
        schemas = stage3_schemas.run(intent, design)
        val     = stage4_validate.run(
            schemas["db"], schemas["api"], schemas["ui"], schemas["auth"]
        )
        elapsed = round(time.time() - t, 1)
        total_time += elapsed
        retries = schemas.get("total_retries", 0)
        total_retries += retries

        status = val["status"]
        if status == "PASS":
            passed += 1

        results.append({
            "prompt": prompt,
            "status": status,
            "errors": len(val["errors"]),
            "warnings": len(val["warnings"]),
            "time_s": elapsed,
        })
        print(f"  {status} | {len(val['errors'])} errors, {len(val['warnings'])} warnings | {elapsed}s")

    except Exception as e:
        elapsed = round(time.time() - t, 1)
        total_time += elapsed
        results.append({
            "prompt": prompt,
            "status": "ERROR",
            "errors": -1,
            "warnings": -1,
            "time_s": elapsed,
        })
        print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Pass rate     : {passed}/{len(PROMPTS)} ({round(passed/len(PROMPTS)*100)}%)")
print(f"  Total retries : {total_retries}")
print(f"  Total time    : {round(total_time)}s  (avg {round(total_time/len(PROMPTS), 1)}s/prompt)")

with open("evaluation/results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n  Results saved to evaluation/results.json")