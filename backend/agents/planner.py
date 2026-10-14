import json
import os
import time
from datetime import datetime
from typing import List, Dict
from sqlmodel import Session, select

from models import HouseholdMember, MealPlan, ConversationMessage
from tools.meal_tools import generate_meal_plan, check_ingredient_safety, validate_meal_against_household
from tools.grocery import consolidate_grocery_list

GROQ_MODEL = "openai/gpt-oss-20b"

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
            "name": "update_meal_plan",
            "description": "Update a specific meal in the current plan.",
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

SYSTEM_PROMPT = """You are Kitchen Agent, a meal planning assistant for a 4-person household.

Members: Sarah (vegetarian), Mike (no restrictions), Emma (child, STRICT peanut allergy - never peanuts), George (grandparent, soft foods, mild spice, diabetic-friendly).

Rules: Every meal safe for ALL. Vegetarian alternative for Sarah when meat is served. No peanuts ever.
Use tools to manage plans. Be concise. No emojis. No em dashes. Use numbered lists for steps, bullets for options. Bold key terms."""


class PlannerAgent:
    def __init__(self, db_session: Session):
        self.session = db_session
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None

    def _get_conversation_history(self) -> List[Dict]:
        messages = self.session.exec(
            select(ConversationMessage)
            .where(ConversationMessage.session_type == "planner")
            .order_by(ConversationMessage.timestamp)
        ).all()
        return [{"role": m.role, "content": m.content} for m in messages[-8:]]

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
            plan_data = generate_meal_plan(member_data, special_requests=tool_input.get("special_requests", ""))
            new_plan = MealPlan(
                week_start=tool_input.get("week_start", "2026-10-14"),
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
        if not self.client:
            return "I need a GROQ_API_KEY set in your .env file to work. Get one free at console.groq.com."

        self._save_message("user", user_message)
        history = self._get_conversation_history()

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        response_text = ""

        try:
            while True:
                for attempt in range(3):
                    try:
                        response = self.client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=messages,
                            tools=PLANNER_TOOLS,
                            tool_choice="auto",
                            max_tokens=400,
                            timeout=30,
                        )
                        break
                    except Exception as e:
                        if "429" in str(e) and attempt < 2:
                            time.sleep(30)
                        else:
                            raise
                msg = response.choices[0].message

                if msg.tool_calls:
                    messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
                        {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in msg.tool_calls
                    ]})
                    for tc in msg.tool_calls:
                        args = json.loads(tc.function.arguments)
                        result = self._execute_tool(tc.function.name, args)
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                else:
                    response_text = msg.content or ""
                    break

        except Exception as e:
            response_text = f"Error: {str(e)}"

        if not response_text:
            response_text = "I processed your request but didn't generate a response. Please try again."

        self._save_message("assistant", response_text)
        return response_text



