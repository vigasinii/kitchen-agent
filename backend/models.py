from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import json

class HouseholdMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    dietary_restrictions: str = Field(default="[]")
    allergies: str = Field(default="[]")
    preferences: str = Field(default="[]")

class MealPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    week_start: str
    status: str = Field(default="planning")
    meals: str = Field(default="{}")

class GroceryList(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meal_plan_id: int = Field(foreign_key="mealplan.id")
    items: str = Field(default="[]")
    status: str = Field(default="pending")

class CookSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meal_plan_id: int = Field(foreign_key="mealplan.id")
    day: str
    meal_type: str = Field(default="dinner")
    meal_name: str
    status: str = Field(default="active")
    notes: str = Field(default="")
    substitutions: str = Field(default="[]")

    outcome_meal: str = Field(default="")
    outcome_notes: str = Field(default="")
    human_interventions: int = Field(default=0)
    completed_at: str = Field(default="")

class ConversationMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_type: str
    role: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ApprovalRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cook_session_id: int = Field(foreign_key="cooksession.id")
    meal_plan_id: int
    day: str
    meal_type: str = Field(default="")
    issue: str
    original_ingredient: str = Field(default="")
    proposed_change: str
    reason: str = Field(default="")
    requested_by: str = Field(default="cook")
    requested_at: str
    status: str = Field(default="pending")
    decided_by: str = Field(default="")
    decided_at: str = Field(default="")
    decision_reason: str = Field(default="")
