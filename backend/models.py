from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import json


class HouseholdMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    dietary_restrictions: str = Field(default="[]")  # JSON list
    allergies: str = Field(default="[]")  # JSON list
    preferences: str = Field(default="[]")  # JSON list


class MealPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    week_start: str  # ISO date string
    status: str = Field(default="planning")  # planning/approved/executing
    meals: str = Field(default="{}")  # JSON 7-day plan


class GroceryList(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meal_plan_id: int = Field(foreign_key="mealplan.id")
    items: str = Field(default="[]")  # JSON list of {name, qty, unit}
    status: str = Field(default="pending")  # pending/ordered/delivered


class CookSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meal_plan_id: int = Field(foreign_key="mealplan.id")
    day: str
    meal_name: str
    status: str = Field(default="active")  # active/completed/cancelled
    notes: str = Field(default="")
    substitutions: str = Field(default="[]")  # JSON list of {missing, substitute, approved}
    # Outcome fields filled when session is completed
    outcome_meal: str = Field(default="")       # what was actually cooked (may differ from plan)
    outcome_notes: str = Field(default="")      # cook's summary of what happened
    human_interventions: int = Field(default=0) # count of approval requests raised
    completed_at: str = Field(default="")


class ConversationMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_type: str  # planner / cook_<id>
    role: str  # user/assistant
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ApprovalRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cook_session_id: int = Field(foreign_key="cooksession.id")
    meal_plan_id: int
    day: str
    meal_type: str = Field(default="")
    issue: str                      # what problem the cook encountered
    original_ingredient: str = Field(default="")
    proposed_change: str            # what the cook wants to do
    reason: str = Field(default="")
    requested_by: str = Field(default="cook")
    requested_at: str
    status: str = Field(default="pending")  # pending/approved/rejected/cancelled
    decided_by: str = Field(default="")
    decided_at: str = Field(default="")
    decision_reason: str = Field(default="")
