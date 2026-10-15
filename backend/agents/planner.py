import json
import os
from datetime import datetime
from typing import List, Dict
from sqlmodel import Session, select

from models import HouseholdMember, MealPlan, ConversationMessage
from tools.meal_tools import generate_meal_plan, check_ingredient_safety, validate_meal_against_household
from tools.grocery import consolidate_grocery_list
from llm_provider import LLMProvider, ProviderError, STATE_CHANGING_TOOLS

PLANNER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_household_members",
            "description": "Get all household members with their dietary restrictions, allergies, and preferences.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_meal_plan",
            "description": "Create a new 7-day meal plan for the household respecting all dietary needs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "week_start": {"type": "string", "description": "ISO date string for the start of the week (YYYY-MM-DD)"},
                    "special_requests": {"type": "string", "description": "Any special requests or theme for the week"}
                },
                "required": ["week_start"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "batch_update_meal_plan",
            "description": "Update multiple meals at once. Encode all updates as a JSON string in updates_json. Example: '[{\"day\":\"Monday\",\"meal_type\":\"dinner\",\"new_meal\":\"Grilled fish\"},{\"day\":\"Tuesday\",\"meal_type\":\"dinner\",\"new_meal\":\"Lentil soup\"}]'",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_id": {"type": "integer", "description": "The meal plan ID"},
                    "updates_json": {"type": "string", "description": "JSON array string of updates, each with day, meal_type, new_meal fields"}
                },
                "required": ["plan_id", "updates_json"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_meal_plan",
            "description": "Update a single meal in the current plan. Use batch_update_meal_plan when changing multiple meals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_id": {"type": "integer", "description": "The meal plan ID"},
                    "day": {"type": "string", "description": "Day of the week (Monday, Tuesday, etc.)"},
                    "meal_type": {"type": "string", "description": "breakfast, lunch, or dinner"},
                    "new_meal": {"type": "string", "description": "The new meal description"}
                },
                "required": ["plan_id", "day", "meal_type", "new_meal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_plan",
            "description": "Get the current active meal plan.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

SYSTEM_PROMPT_BASE = """You are Riya, the household's meal planner. You know this family well and genuinely care about feeding them well. You have strong opinions about food and you're not shy about sharing them. You get excited when a week's plan comes together beautifully.

{household_summary}

Your personality:
- Warm and direct. You speak like a knowledgeable friend, not a customer service bot.
- You refer to household members by name naturally ("Emma will love this", "George needs this soft").
- You notice when something is a good idea and say so. You push back gently when a request conflicts with someone's needs.
- Short sentences. Plain language. Never stiff or corporate.
- You never suggest anything unsafe, but you explain why in a human way, not a warning label.

Hard rules: every meal safe for ALL members. Strict allergens never included. Vegetarian alternative whenever meat is served.
Use tools to fetch and update plans. When updating multiple meals (e.g. all dinners), use batch_update_meal_plan with all changes in one call instead of calling update_meal_plan repeatedly. No emojis. No em dashes. Numbered lists for steps, bullets for options."""

MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "5"))


class PlannerAgent:
    def __init__(self, db_session: Session):
        self.session = db_session
        self.provider = LLMProvider()

    def _build_system_prompt(self) -> str:
        members = self.session.exec(select(HouseholdMember)).all()
        if members:
            lines = []
            for m in members:
                restrictions = json.loads(m.dietary_restrictions)
                allergies = json.loads(m.allergies)
                parts = []
                if restrictions:
                    parts.append(f"diet: {', '.join(restrictions)}")
                if allergies:
                    parts.append(f"allergies: {', '.join(allergies)} (STRICT)")
                lines.append(f"- {m.name}: {'; '.join(parts) if parts else 'no restrictions'}")
            summary = "Household members:\n" + "\n".join(lines)
        else:
            summary = "Household: no members configured yet."
        return SYSTEM_PROMPT_BASE.format(household_summary=summary)

    def _get_conversation_history(self) -> List[Dict]:
        messages = self.session.exec(
            select(ConversationMessage)
            .where(ConversationMessage.session_type == "planner")
            .order_by(ConversationMessage.timestamp)
        ).all()
        return [{"role": m.role, "content": m.content} for m in messages[-4:]]

    def _save_message(self, role: str, content: str):
        msg = ConversationMessage(
            session_type="planner",
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat()
        )
        self.session.add(msg)
        self.session.commit()

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        if tool_name == "get_household_members":
            members = self.session.exec(select(HouseholdMember)).all()
            result = [
                {
                    "id": m.id,
                    "name": m.name,
                    "dietary_restrictions": json.loads(m.dietary_restrictions),
                    "allergies": json.loads(m.allergies),
                    "preferences": json.loads(m.preferences)
                }
                for m in members
            ]
            return json.dumps(result)

        elif tool_name == "create_meal_plan":
            members = self.session.exec(select(HouseholdMember)).all()
            member_data = [
                {
                    "name": m.name,
                    "dietary_restrictions": json.loads(m.dietary_restrictions),
                    "allergies": json.loads(m.allergies),
                    "preferences": json.loads(m.preferences)
                }
                for m in members
            ]
            try:
                plan_data = generate_meal_plan(member_data, special_requests=tool_input.get("special_requests", ""))
            except Exception as e:
                print(f"[PLANNER] generate_meal_plan failed: {type(e).__name__}: {str(e)[:300]}")
                return json.dumps({"error": f"Meal plan generation failed: {type(e).__name__}. Do not retry — report this to the user."})
            week_start = tool_input.get("week_start") or datetime.utcnow().strftime("%Y-%m-%d")
            new_plan = MealPlan(
                week_start=week_start,
                status="planning",
                meals=json.dumps(plan_data["plan"])
            )
            self.session.add(new_plan)
            self.session.commit()
            self.session.refresh(new_plan)
            return json.dumps({"plan_id": new_plan.id, "plan": plan_data["plan"], "notes": plan_data["notes"]})

        elif tool_name == "update_meal_plan":
            plan = self.session.get(MealPlan, tool_input["plan_id"])
            if not plan:
                return json.dumps({"error": "Plan not found"})
            # Safety check before saving
            members = self.session.exec(select(HouseholdMember)).all()
            member_data = [
                {"name": m.name, "dietary_restrictions": json.loads(m.dietary_restrictions), "allergies": json.loads(m.allergies)}
                for m in members
            ]
            safety = validate_meal_against_household(tool_input["new_meal"], member_data)
            if not safety["safe"]:
                critical = [v for v in safety["violations"] if v["severity"] == "CRITICAL"]
                return json.dumps({
                    "error": "Meal rejected: safety violations detected",
                    "violations": safety["violations"],
                    "recommendation": "Choose a different meal that avoids these conflicts",
                    "critical_count": len(critical)
                })
            meals = json.loads(plan.meals)
            day = tool_input["day"]
            meal_type = tool_input["meal_type"]
            if day in meals:
                meals[day][meal_type] = tool_input["new_meal"]
                plan.meals = json.dumps(meals)
                self.session.add(plan)
                self.session.commit()
                # Auto-regenerate grocery list if one exists for this plan
                from models import GroceryList
                from sqlmodel import select as sql_select
                from tools.grocery import consolidate_grocery_list
                existing_grocery = self.session.exec(
                    sql_select(GroceryList).where(GroceryList.meal_plan_id == plan.id)
                ).first()
                grocery_note = ""
                if existing_grocery:
                    items = consolidate_grocery_list(meals)
                    existing_grocery.items = json.dumps(items)
                    existing_grocery.status = "pending"
                    self.session.add(existing_grocery)
                    self.session.commit()
                    grocery_note = " Grocery list regenerated automatically."
                return json.dumps({"success": True, "updated": f"{day} {meal_type} -> {tool_input['new_meal']}", "safety": "passed", "note": grocery_note.strip()})
            return json.dumps({"error": f"Day {day} not found in plan"})

        elif tool_name == "batch_update_meal_plan":
            plan = self.session.get(MealPlan, tool_input["plan_id"])
            if not plan:
                return json.dumps({"error": "Plan not found"})
            raw_updates = tool_input.get("updates_json", "")
            try:
                updates = json.loads(raw_updates) if isinstance(raw_updates, str) else raw_updates
            except (json.JSONDecodeError, TypeError) as e:
                return json.dumps({"error": f"Invalid updates_json: {e}"})
            if not updates:
                return json.dumps({"error": "No updates provided"})

            members = self.session.exec(select(HouseholdMember)).all()
            member_data = [
                {"name": m.name, "dietary_restrictions": json.loads(m.dietary_restrictions), "allergies": json.loads(m.allergies)}
                for m in members
            ]
            # Validate all changes before applying any
            violations = []
            for u in updates:
                safety = validate_meal_against_household(u["new_meal"], member_data)
                if not safety["safe"]:
                    violations.append({"day": u["day"], "meal_type": u["meal_type"], "violations": safety["violations"]})
            if violations:
                return json.dumps({"error": "Batch rejected: safety violations detected", "violations": violations})

            meals = json.loads(plan.meals)
            applied = []
            skipped = []
            for u in updates:
                day, meal_type, new_meal = u["day"], u["meal_type"], u["new_meal"]
                if day in meals:
                    meals[day][meal_type] = new_meal
                    applied.append(f"{day} {meal_type}")
                else:
                    skipped.append(day)

            plan.meals = json.dumps(meals)
            self.session.add(plan)
            self.session.commit()

            # Regenerate grocery list if one exists
            from models import GroceryList
            from sqlmodel import select as sql_select
            existing_grocery = self.session.exec(
                sql_select(GroceryList).where(GroceryList.meal_plan_id == plan.id)
            ).first()
            if existing_grocery:
                items = consolidate_grocery_list(meals)
                existing_grocery.items = json.dumps(items)
                existing_grocery.status = "pending"
                self.session.add(existing_grocery)
                self.session.commit()

            return json.dumps({
                "success": True,
                "applied_count": len(applied),
                "applied": applied,
                "skipped": skipped,
                "plan_id": plan.id,
            })

        elif tool_name == "get_current_plan":
            plans = self.session.exec(select(MealPlan).order_by(MealPlan.id.desc())).all()
            if not plans:
                return json.dumps({"error": "No meal plans found"})
            latest = plans[0]
            return json.dumps({
                "id": latest.id,
                "week_start": latest.week_start,
                "status": latest.status,
                "meals": json.loads(latest.meals)
            })

        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def chat(self, user_message: str) -> str:
        """
        Returns the agent response text.
        Raises ProviderError when all LLM providers fail unrecoverably.
        """
        self._save_message("user", user_message)
        history = self._get_conversation_history()

        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}] + history
        response_text = ""
        executed_state_tools: dict = {}  # key -> result, prevents duplicate DB writes
        all_tool_calls: dict = {}  # key -> call count, detects read-tool loops
        completed_successfully = False

        for round_num in range(MAX_TOOL_ROUNDS):
            resp, provider, model = self.provider.call(messages, PLANNER_TOOLS)
            msg = resp.choices[0].message
            print(f"[PLANNER] round={round_num+1} provider={provider} model={model} has_tool_calls={bool(msg.tool_calls)}")

            if msg.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in msg.tool_calls
                    ],
                })
                stale = False
                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"[PLANNER] malformed tool args for {tc.function.name}: {e}")
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps({"error": "Malformed tool arguments — please simplify your request."})})
                        continue
                    dedup_key = (tc.function.name, tc.function.arguments)

                    # Break loop if same tool+args called 3+ times
                    all_tool_calls[dedup_key] = all_tool_calls.get(dedup_key, 0) + 1
                    if all_tool_calls[dedup_key] >= 3:
                        print(f"[PLANNER] loop detected: {tc.function.name} called {all_tool_calls[dedup_key]}x with same args")
                        stale = True
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps({"error": "repeated call detected, stopping loop"})})
                        continue

                    if tc.function.name in STATE_CHANGING_TOOLS and dedup_key in executed_state_tools:
                        result = executed_state_tools[dedup_key]
                        print(f"[PLANNER] step={round_num+1} tool={tc.function.name} dedup_hit=true")
                    else:
                        result = self._execute_tool(tc.function.name, args)
                        result_obj = json.loads(result) if result else {}
                        success = "error" not in result_obj
                        print(f"[PLANNER] step={round_num+1} tool={tc.function.name} success={success} result_len={len(result)}")
                        # Only cache successful state-changing calls; errors must be retried
                        if tc.function.name in STATE_CHANGING_TOOLS and success:
                            executed_state_tools[dedup_key] = result

                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

                if stale:
                    break
            else:
                response_text = msg.content or ""
                completed_successfully = True
                break

        if not completed_successfully and not response_text:
            # Check if any state-changing tool succeeded — if so don't claim failure
            if executed_state_tools:
                print(f"[PLANNER] hit step limit but {len(executed_state_tools)} state changes succeeded")
                response_text = "Done. The changes have been saved, but I ran out of steps before summarising them. Please check the plan page."
            else:
                response_text = "I could not complete this in time. Please try a simpler request."

        if not response_text:
            response_text = "I could not generate a response. Please try again."

        self._save_message("assistant", response_text)
        return response_text



