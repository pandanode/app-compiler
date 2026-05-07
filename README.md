# App Compiler — Natural Language → Production App Schema

> **Turn a one-line description into a fully validated, production-ready app specification in minutes.**
> Built as a demonstration of LLM orchestration, schema enforcement, and intelligent repair systems.

---

## What is this?

Most people use LLMs like a search engine — one prompt, one answer, hope for the best.

This project treats LLMs like a **compiler**. Your natural language description enters a strict 4-stage pipeline. Each stage has a defined input contract, a defined output contract, and a validation layer that catches and repairs errors before they propagate. The output is a complete, cross-validated app specification — database schema, API schema, UI schema, and auth rules — ready to power a code generator or runtime.

**Input:**
```
Build a CRM with login, contacts, dashboard, role-based access, and subscription payments.
```

**Output:** A validated JSON specification covering every layer of the application stack.

---

## Pipeline Architecture

```
User Prompt (natural language)
        │
        ▼
┌─────────────────────────────┐
│  Stage 1 — Intent Extraction │   Parse entities, roles, features, constraints
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Stage 2 — System Design    │   Architecture, relationships, user flows, routes
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  Stage 3 — Schema Generation (4 parallel LLM calls) │
│                                                     │
│   DB Schema    API Schema    UI Schema    Auth Rules │
└─────────────┬───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Stage 4 — Validation +     │   Cross-layer consistency checks
│  Repair Engine              │   Role integrity, endpoint mapping, field matching
└─────────────┬───────────────┘
              │
              ▼
     Validated App JSON Spec
```

Each stage's output is the next stage's input contract — enforced by Pydantic schemas. If the LLM returns malformed output, the repair engine sends the exact error back and requests a targeted fix. No blind retries.

---

## Evaluation Results

Tested across 20 prompts — 10 real product specs, 10 edge cases (vague, conflicting, underspecified).

| Metric | Result |
|---|---|
| Real prompts pass rate | **10 / 10 (100%)** |
| Edge cases handled | **10 / 10 (100%)** |
| Average retries per run | **0.1** |
| Average latency (free tier) | **~173s** |
| Validation errors (hard failures) | **0** |

The repair engine caught and resolved schema mismatches, JSON syntax errors, and structural mistakes — without a single full pipeline failure across all 20 test cases.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| LLM Orchestration | OpenRouter API | Model-agnostic, free tier available |
| Schema Validation | Pydantic v2 | Strict type enforcement, clear error messages |
| Repair Engine | Custom | Targeted fix, not blind retry |
| API Server | FastAPI | Async, fast, automatic docs |
| Frontend | Vanilla HTML/JS | Zero dependencies, instant load |

---

## Project Structure

The codebase is organized around pipeline separation — each stage is an independent module with a single responsibility.

**`pipeline/`** contains the 4 execution stages plus the repair engine. Each stage file exports one function: `run()`.

**`schemas/`** contains Pydantic models that define the data contracts between stages. These are the source of truth for what valid output looks like at every boundary.

**`evaluation/`** contains the test harness — 20 prompts and a runner that measures pass rate, retry count, and latency.

**`frontend/`** is a single HTML file with a live stage-by-stage progress display.

---

## Running Locally

**Prerequisites:** Python 3.11+, an OpenRouter API key (free at openrouter.ai)

```bash
git clone https://github.com/pandanode/app-compiler
cd app-compiler
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a `.env` file:
```
OPENROUTER_API_KEY=your-key-here
```

Start the server:
```bash
uvicorn main:app --reload
```

Open `http://localhost:8000` — type any app description, click Compile.

---

## Running the Evaluation

```bash
python evaluation/eval_runner.py
```

Runs all 20 test prompts, prints pass rate, retry count, and latency, and saves results to `evaluation/results.json`.

---

## API

**POST `/compile`**

```json
{
  "prompt": "Build a SaaS analytics dashboard with teams and billing"
}
```

Returns a fully validated JSON object containing intent, system design, database schema, API schema, UI schema, auth rules, validation status, and retry count.

---

## Key Design Decisions

**Why multi-stage instead of one prompt?**
A single prompt asking for DB schema + API schema + UI schema + auth rules produces inconsistent output — field names don't match, roles are invented, endpoints don't align. Staging forces each layer to be built on top of validated previous output, and allows targeted repair when something breaks.

**Why Pydantic and not JSON Schema?**
Pydantic gives Python-native validation with clear error messages that can be fed directly back to the LLM for repair. The error `Input should be a valid string [type=string_type]` is more actionable than a raw JSON Schema violation.

**Why targeted repair instead of full retry?**
Full retry is expensive and often reproduces the same error. Sending the exact Pydantic error back with the bad output as context results in a correct fix in one additional call over 95% of the time.

**Why not a faster paid model?**
The free OpenRouter model adds ~3 min latency. The architecture is model-agnostic — swapping to GPT-4o or Claude Sonnet requires changing one line and reduces total latency to under 20 seconds. The design decision was to demonstrate the system works correctly before optimizing for speed.

---

## What This Is Not

This is not a prompt engineering project. There is no magic prompt that makes this work. The reliability comes from the architecture — strict contracts at every stage boundary, a repair engine that treats LLM errors as recoverable exceptions, and cross-layer validation that catches inconsistencies before they reach the output.

---

## Author

Built for the AI Platform Engineer (Founding Intern) demo task.
The objective: design a system that behaves like a compiler for software generation.