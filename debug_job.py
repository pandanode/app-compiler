# debug_job.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import stage1_intent, stage2_design, stage3_schemas, stage4_validate
import json

prompt = "Build a job board with listings, applications, and employer profiles."
intent  = stage1_intent.run(prompt)
design  = stage2_design.run(intent)
schemas = stage3_schemas.run(intent, design)
val     = stage4_validate.run(schemas["db"], schemas["api"], schemas["ui"], schemas["auth"])

print("\nERRORS:")
for e in val["errors"]:
    print(" ", e)
print("\nAuth roles:", schemas["auth"].roles)