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

    def get_dietary_restrictions(self):
        return json.loads(self.dietary_restrictions)

    def get_allergies(self):
        return json.loads(self.allergies)

    def get_preferences(self):
        return json.loads(self.preferences)


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
    day: str  # e.g., "Monday"
    meal_name: str
    status: str = Field(default="active")  # active/completed/cancelled
    notes: str = Field(default="")
    substitutions: str = Field(default="[]")  # JSON list


class ConversationMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_type: str  # planner/cook
    role: str  # user/assistant
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
