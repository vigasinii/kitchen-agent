# Kitchen Agent

A voice-first household meal planning and cooking assistant. Two AI agents handle the full loop: the Planner Agent works with the household to create a constraint-aware weekly meal plan, and the Cook Agent guides the cook through daily execution with real-time substitution help and an approval workflow.

## Stack

- **Backend**: FastAPI + SQLite (via SQLModel)
- **AI**: Groq API (`openai/gpt-oss-120b` primary, `openai/gpt-oss-20b` fallback) with tool-use loops
- **Frontend**: React 18 (CDN, no build step), Web Speech API
- **Deploy**: Render (backend) + Vercel (frontend)

## Running locally

**Requirements**: Python 3.10+, a [Groq API key](https://console.groq.com)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # add your GROQ_API_KEY
uvicorn main:app --port 8000
```

Open `frontend/index.html` in your browser (or serve the frontend folder with any static server).

## Running evaluations

```bash
cd backend
python evals.py
```

Runs 18 scenario groups (allergy enforcement, vegetarian constraints, ingredient safety, dairy allergy, conflicting preferences, empty household fallback, budget-constrained, time-constrained, substitution chains, approval state transitions, rejection unchanged plan, grocery regeneration, duplicate approval prevention, API failure degradation, cook session completion) with 30+ individual checks. Exit code 0 = all passed.

## Demo household

| Name   | Role        | Key constraints                               |
|--------|-------------|-----------------------------------------------|
| Sarah  | Adult       | Vegetarian, no meat                          |
| Mike   | Adult       | No restrictions                              |
| Emma   | Child (~8)  | Severe peanut allergy (life-critical)        |
| George | Grandparent | Soft foods, mild spice, diabetic-friendly    |

A 7-day meal plan and grocery list are seeded on first launch so the UI is populated before you chat.

## Using the app

**Planner tab**: chat to generate or adjust the week's meals. Voice input via mic button. Try:
- "Plan a new week with more Indian food"
- "Can we swap Tuesday dinner for something lighter for George?"
- "Is cashew cream safe for Emma?"

**Cook tab**: select a day and meal, click Start Cooking, then get step-by-step guidance. Try:
- "I don't have salmon, what can I substitute?"
- "Emma has a friend over, can we make the dessert nut-free?"
- "The household needs to approve skipping tonight's planned meal"

**Meal Plan tab**: 7-day grid, approve the plan to lock it in.

**Grocery tab**: consolidated shopping list, click Order via Instamart to simulate ordering.

**Approvals tab**: household approval requests raised by Annie appear here. Approve or reject each one — approving a substitution updates the meal plan automatically.

## Project structure

```
backend/
  main.py            FastAPI routes (household, meal plans, grocery, cook sessions, approvals)
  database.py        SQLite setup and demo seed
  models.py          SQLModel table definitions
  agents/
    planner.py       Planner Agent: LLM tool-use loop, safety validation before saves
    cook.py          Cook Agent: real-time guidance, substitution, approval flagging
  tools/
    meal_tools.py    Dynamic LLM meal generation, pre-save safety validator
    grocery.py       Grocery consolidation, Instamart simulation
  evals.py           Repeatable evaluation suite
frontend/
  index.html
  app.js             React components, voice input/output
  styles.css
```

## What is real vs. simulated

| Feature | Status |
|---|---|
| AI meal planning (constraint-aware, LLM-generated) | Real (Groq) |
| Pre-save safety validation (allergy + dietary) | Real (blocks unsafe meals) |
| Voice input/output | Real (Web Speech API) |
| Household profiles + restrictions | Real (SQLite) |
| Cook-to-household approval workflow | Real (flagged in session, household approves/rejects via API) |
| Grocery list generation | Real (rule-based consolidation from meal plan) |
| Instamart ordering | Simulated (returns mock order ID and ETA) |
