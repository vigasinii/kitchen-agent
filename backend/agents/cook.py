import json
import os
import time
from datetime import datetime
from typing import List, Dict
from sqlmodel import Session, select

from models import HouseholdMember, MealPlan, CookSession, ConversationMessage, ApprovalRequest
from tools.meal_tools import check_ingredient_safety

GROQ_MODEL = "qwen/qwen3.8-27b"

COOK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_todays_meal",
            "description": "Get the planned meal for a specific day and meal type from the current meal plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {"type": "string", "description": "Day of the week (Monday, Tuesday, etc.)"},
                    "meal_type": {"type": "string", "description": "breakfast, lunch, or dinner"}
                },
                "required": ["day", "meal_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "report_missing_ingredient",
            "description": "Report that an ingredient is missing and get substitution suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredient": {"type": "string", "description": "The missing ingredient"},
                    "for_recipe": {"type": "string", "description": "The recipe it was needed for"},
                    "cook_session_id": {"type": "integer", "description": "Current cook session ID"}
                },
                "required": ["ingredient", "for_recipe", "cook_session_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_substitution",
            "description": "Suggest safe ingredient substitutions considering all household dietary needs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "original_ingredient": {"type": "string", "description": "The original ingredient"},
                    "reason": {"type": "string", "description": "Why it needs to be substituted"}
                },
                "required": ["original_ingredient", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_cook_session",
            "description": "Update the cook session with notes or status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cook_session_id": {"type": "integer", "description": "Cook session ID to update"},
                    "notes": {"type": "string", "description": "Notes to add to the session"},
                    "status": {"type": "string", "description": "New status: active, completed, or cancelled"}
                },
                "required": ["cook_session_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_session",
            "description": "Mark the cook session as completed and record the outcome: what was actually cooked, any deviations from the plan, and a summary of what required human intervention.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cook_session_id": {"type": "integer", "description": "Cook session ID"},
                    "outcome_meal": {"type": "string", "description": "What was actually cooked (may differ from the plan if substitutions were made)"},
                    "outcome_notes": {"type": "string", "description": "Brief summary: what went smoothly, what went wrong, what needed human decisions"},
                    "followed_plan": {"type": "boolean", "description": "Whether the original plan was followed without changes"}
                },
                "required": ["cook_session_id", "outcome_meal", "outcome_notes", "followed_plan"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "flag_household_approval_needed",
            "description": "Flag that a significant change needs household approval before proceeding. Creates a structured approval request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue": {"type": "string", "description": "What problem the cook encountered"},
                    "proposed_change": {"type": "string", "description": "What change is proposed"},
                    "cook_session_id": {"type": "integer", "description": "Cook session ID"},
                    "meal_plan_id": {"type": "integer", "description": "Meal plan ID (optional)"},
                    "day": {"type": "string", "description": "Day of the week this affects (optional)"},
                    "meal_type": {"type": "string", "description": "Meal type this affects: breakfast, lunch, or dinner (optional)"},
                    "original_ingredient": {"type": "string", "description": "The original ingredient being substituted (optional)"},
                    "reason": {"type": "string", "description": "Why the change is needed (optional)"}
                },
                "required": ["issue", "proposed_change", "cook_session_id"]
            }
        }
    }
]

GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = """You are Arjun, the household's cook guide. You have years of kitchen experience and you're calm under pressure. You've cooked for this family enough times that you know their quirks. You keep things moving.

{household_summary}

Your personality:
- Steady and reassuring. When something goes wrong in the kitchen, you don't panic, you problem-solve.
- Practical above all. You give the cook what they need to know right now, not a lecture.
- You remember who you're cooking for. If a substitution touches an allergy, you flag it immediately and clearly.
- Short, numbered steps when guiding. One thing at a time.
- Honest about trade-offs: "This will change the texture a bit, but it'll still be good."

Workflow: get the planned meal, guide step by step, handle problems as they come, flag anything big for household approval, record what was actually cooked at the end.
Allergens are non-negotiable. Use flag_household_approval_needed for significant changes. Always end with complete_session.
No emojis. No em dashes. Numbered steps for instructions. Bullets for options."""

SUBSTITUTION_MAP = {
    "butter": ["olive oil", "coconut oil", "vegan butter"],
    "milk": ["oat milk", "almond milk (tree nuts OK for Emma)", "soy milk"],
    "eggs": ["flax egg (1 tbsp flax + 3 tbsp water)", "applesauce (for baking)", "mashed banana"],
    "chicken": ["chickpeas (V)", "tofu (V)", "tempeh (V)", "turkey"],
    "beef": ["lentils (V)", "mushrooms (V)", "turkey"],
    "cream": ["coconut cream", "cashew cream (tree nut - verify allergy)", "silken tofu"],
    "parmesan": ["nutritional yeast (V)", "vegan parmesan"],
    "soy sauce": ["coconut aminos", "tamari (GF)"],
    "pasta": ["rice", "zucchini noodles", "cauliflower rice"],
    "bread crumbs": ["crushed crackers", "rolled oats", "crushed rice cakes"],
    "sugar": ["honey", "maple syrup", "stevia (good for George)"],
}


class CookAgent:
    def __init__(self, db_session: Session):
        self.session = db_session
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None

    def _get_conversation_history(self, cook_session_id: int) -> List[Dict]:
        session_tag = f"cook_{cook_session_id}"
        messages = self.session.exec(
            select(ConversationMessage)
            .where(ConversationMessage.session_type == session_tag)
            .order_by(ConversationMessage.timestamp)
        ).all()
        return [{"role": m.role, "content": m.content} for m in messages[-8:]]

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
                    parts.append(f"allergies: {', '.join(allergies)} (STRICT - never suggest)")
                lines.append(f"- {m.name}: {'; '.join(parts) if parts else 'no restrictions'}")
            summary = "Household:\n" + "\n".join(lines)
        else:
            summary = "Household: no members configured yet."
        return SYSTEM_PROMPT.format(household_summary=summary)

    def _save_message(self, role: str, content: str, cook_session_id: int):
        session_tag = f"cook_{cook_session_id}"
        msg = ConversationMessage(
            session_type=session_tag,
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat()
        )
        self.session.add(msg)
        self.session.commit()

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        if tool_name == "get_todays_meal":
            plans = self.session.exec(select(MealPlan).order_by(MealPlan.id.desc())).all()
            if not plans:
                return json.dumps({"error": "No meal plan found"})
            plan = plans[0]
            meals = json.loads(plan.meals)
            day = tool_input.get("day", "Monday")
            meal_type = tool_input.get("meal_type", "dinner")
            if day in meals and meal_type in meals[day]:
                return json.dumps({"day": day, "meal_type": meal_type, "meal": meals[day][meal_type], "plan_status": plan.status})
            return json.dumps({"error": f"No {meal_type} found for {day}"})

        elif tool_name == "report_missing_ingredient":
            cook_session_id = tool_input.get("cook_session_id")
            ingredient = tool_input["ingredient"]
            substitutes = SUBSTITUTION_MAP.get(ingredient.lower(), [])

            if cook_session_id:
                cook_session = self.session.get(CookSession, cook_session_id)
                if cook_session:
                    subs = json.loads(cook_session.substitutions)
                    subs.append({"missing": ingredient, "for_recipe": tool_input.get("for_recipe", "unknown"), "reported_at": datetime.utcnow().isoformat()})
                    cook_session.substitutions = json.dumps(subs)
                    self.session.add(cook_session)
                    self.session.commit()

            return json.dumps({
                "ingredient": ingredient,
                "suggested_substitutes": substitutes if substitutes else ["No direct substitute found - check pantry"],
                "note": "Check all substitutes against Emma's peanut allergy and George's dietary needs"
            })

        elif tool_name == "suggest_substitution":
            ingredient = tool_input["original_ingredient"].lower()
            subs = SUBSTITUTION_MAP.get(ingredient, [])
            members = self.session.exec(select(HouseholdMember)).all()
            member_data = [{"name": m.name, "dietary_restrictions": json.loads(m.dietary_restrictions), "allergies": json.loads(m.allergies)} for m in members]
            safe_subs = []
            for sub in subs:
                safety = check_ingredient_safety(sub, member_data)
                safe_subs.append({"substitute": sub, "safe": safety["safe"], "conflicts": safety["conflicts"]})
            return json.dumps({
                "original": tool_input["original_ingredient"],
                "reason": tool_input["reason"],
                "substitutions": safe_subs if safe_subs else [{"substitute": "No known substitutes", "safe": True, "conflicts": []}]
            })

        elif tool_name == "update_cook_session":
            cook_session_id = tool_input.get("cook_session_id")
            cook_session = self.session.get(CookSession, cook_session_id)
            if not cook_session:
                return json.dumps({"error": "Cook session not found"})
            if "notes" in tool_input:
                existing = cook_session.notes or ""
                cook_session.notes = (existing + "\n" + tool_input["notes"]).strip()
            if "status" in tool_input:
                cook_session.status = tool_input["status"]
            self.session.add(cook_session)
            self.session.commit()
            return json.dumps({"success": True, "session_id": cook_session_id, "status": cook_session.status})

        elif tool_name == "complete_session":
            cook_session_id = tool_input.get("cook_session_id")
            cook_session = self.session.get(CookSession, cook_session_id)
            if not cook_session:
                return json.dumps({"error": "Cook session not found"})
            # Count approval requests from both notes (legacy) and ApprovalRequest table
            notes = cook_session.notes or ""
            notes_count = notes.count("[APPROVAL NEEDED]") + notes.count("[APPROVED]") + notes.count("[REJECTED]")
            db_count = len(self.session.exec(
                select(ApprovalRequest).where(ApprovalRequest.cook_session_id == cook_session_id)
            ).all())
            interventions = max(notes_count, db_count)
            cook_session.status = "completed"
            cook_session.outcome_meal = tool_input.get("outcome_meal", cook_session.meal_name)
            cook_session.outcome_notes = tool_input.get("outcome_notes", "")
            cook_session.human_interventions = interventions
            cook_session.completed_at = datetime.utcnow().isoformat()
            self.session.add(cook_session)
            self.session.commit()
            deviated = not tool_input.get("followed_plan", True)
            return json.dumps({
                "success": True,
                "session_id": cook_session_id,
                "status": "completed",
                "followed_plan": tool_input.get("followed_plan"),
                "outcome_meal": cook_session.outcome_meal,
                "human_interventions": interventions,
                "message": "Session recorded. The outcome has been logged for household review." + (
                    " The plan was followed without changes." if not deviated
                    else f" Note: the meal deviated from the plan ({cook_session.outcome_meal})."
                )
            })

        elif tool_name == "flag_household_approval_needed":
            cook_session_id = tool_input.get("cook_session_id")
            cook_session = self.session.get(CookSession, cook_session_id)

            approval_id = None

            if cook_session:
                # Legacy notes-based tracking
                note = f"[APPROVAL NEEDED] {tool_input['issue']} - Proposed: {tool_input['proposed_change']}"
                existing = cook_session.notes or ""
                cook_session.notes = (existing + "\n" + note).strip()
                self.session.add(cook_session)
                self.session.commit()

                # Structured ApprovalRequest record
                approval = ApprovalRequest(
                    cook_session_id=cook_session_id,
                    meal_plan_id=tool_input.get("meal_plan_id") or cook_session.meal_plan_id,
                    day=tool_input.get("day") or cook_session.day or "",
                    meal_type=tool_input.get("meal_type", ""),
                    issue=tool_input["issue"],
                    original_ingredient=tool_input.get("original_ingredient", ""),
                    proposed_change=tool_input["proposed_change"],
                    reason=tool_input.get("reason", ""),
                    requested_by="cook",
                    requested_at=datetime.utcnow().isoformat(),
                    status="pending",
                )
                self.session.add(approval)
                self.session.commit()
                self.session.refresh(approval)
                approval_id = approval.id

            return json.dumps({
                "flagged": True,
                "approval_id": approval_id,
                "issue": tool_input["issue"],
                "proposed_change": tool_input["proposed_change"],
                "message": "Issue flagged for household review. Approval request created.",
                "next_step": "Wait for household to approve or reject via /approvals/{approval_id}/decide"
            })

        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def chat(self, user_message: str, cook_session_id: int) -> str:
        if not self.client:
            return "I need a GROQ_API_KEY set in your .env file to work. Get one free at console.groq.com."

        self._save_message("user", user_message, cook_session_id)
        history = self._get_conversation_history(cook_session_id)

        cook_session = self.session.get(CookSession, cook_session_id)
        context = ""
        if cook_session:
            context = f"\n\nCurrent session: Day={cook_session.day}, Meal={cook_session.meal_name}, Status={cook_session.status}"

        system_prompt = self._build_system_prompt() + context
        messages = [{"role": "system", "content": system_prompt}] + history
        response_text = ""

        def groq_call():
            for attempt in range(2):
                try:
                    return self.client.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=messages,
                        tools=COOK_TOOLS,
                        tool_choice="auto",
                        max_tokens=500,
                        timeout=30,
                    )
                except Exception as e:
                    if "429" in str(e) and attempt == 0:
                        time.sleep(5)
                    else:
                        raise

        try:
            for round_num in range(MAX_TOOL_ROUNDS):
                response = groq_call()
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
            else:
                response_text = "I reached the maximum number of steps. Please try a simpler request."

        except Exception as e:
            response_text = f"Error: {str(e)}"

        if not response_text:
            response_text = "I could not generate a response. Please try again."

        self._save_message("assistant", response_text, cook_session_id)
        return response_text

