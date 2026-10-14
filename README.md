# Anyaa Kitchen OS

A voice-first household meal planning and execution assistant for a 4-person household.

---

## Setup

### 1. Install dependencies

```bash
cd kitchen-os/backend
pip install -r requirements.txt
```

### 2. Set your API key

Create a `.env` file in the `backend/` directory:

```
ANTHROPIC_API_KEY=your-key-here
```

Without this key the app still runs and serves UI + seeded data, but the AI chat features will return a friendly error message.

### 3. Run the server

```bash
cd kitchen-os/backend
uvicorn main:app --reload
```

The app serves both the API and the frontend at http://localhost:8000

---

## Demo Household

The app seeds a 4-person household on first launch:

| Name   | Role        | Key restrictions                              |
|--------|-------------|-----------------------------------------------|
| Sarah  | Adult       | Vegetarian — no meat                         |
| Mike   | Adult       | No restrictions                               |
| Emma   | Child (~8)  | **Severe peanut allergy** + kid-friendly food |
| George | Grandparent | Soft foods, mild spice, diabetic-friendly     |

A full approved 7-day meal plan and grocery list are seeded automatically so the UI is populated before you use the AI.

---

## Using the App

### Planner Tab
Chat with Anyaa to plan or adjust the week's meals. Voice input via the mic button — your browser's Web Speech API captures audio, Anyaa responds in text and speaks the reply aloud.

Try:
- "What's on the plan for Wednesday dinner?"
- "Can we swap Saturday lunch for something lighter?"
- "Is pesto safe for Emma?"

### Cook Tab
Select a day and meal, click **Start Cooking**, then chat with the Cook Copilot for step-by-step guidance, timing, and substitution help.

Try:
- "I don't have mozzarella, what can I use?"
- "How long does the salmon need in the oven?"
- "Emma is helping me today, what should she do first?"

### Meal Plan Tab
7-day calendar grid. Click **Approve Plan** to confirm the week's meals.

### Grocery List Tab
Consolidated shopping list derived from the meal plan, grouped by category. Click **Order via Instamart** to simulate placing a grocery order (returns a fake order ID and ETA).

---

## Architecture

```
browser (React 18 via CDN)
    ↕ HTTP/JSON
FastAPI backend (Python)
    ├── /chat/planner → PlannerAgent (Anthropic tool-use loop)
    ├── /chat/cook    → CookAgent   (Anthropic tool-use loop)
    ├── SQLite via SQLModel (models: HouseholdMember, MealPlan, GroceryList, CookSession, ConversationMessage)
    └── Static file mount → serves frontend/
```

Both agents use a tool-use agentic loop: the model requests tools (e.g. `get_household_members`, `suggest_substitution`), the backend executes the Python function, sends back `tool_result`, and the model continues until it produces a final text response.

Conversation history is persisted in SQLite so context survives page reloads.

---

## What is Real vs Simulated

| Feature | Status |
|---|---|
| AI chat (Planner + Cook) | Real — Claude claude-haiku-4-5 via Anthropic API |
| Voice input | Real — browser Web Speech API (Chrome/Edge) |
| Voice output | Real — browser SpeechSynthesis API |
| Household data | Seeded demo data, real DB (SQLite) |
| Meal plan generation | Demo plan hard-coded; AI can modify via tools |
| Ingredient safety checks | Real logic against allergen map |
| Grocery list | Derived from meal plan via ingredient database |
| Instamart order | **Simulated** — returns fake order ID, ETA, cost |
| Grocery delivery | **Simulated** — no real integration |
