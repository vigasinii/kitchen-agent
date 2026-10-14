import json
import os
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import engine, get_session, init_db
from models import HouseholdMember, MealPlan, GroceryList, CookSession, ConversationMessage
from tools.grocery import consolidate_grocery_list, simulate_instamart_order

app = FastAPI(title="Anyaa Kitchen OS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Pydantic Request Models ----

class HouseholdMemberCreate(BaseModel):
    name: str
    dietary_restrictions: List[str] = []
    allergies: List[str] = []
    preferences: List[str] = []


class MealPlanCreate(BaseModel):
    week_start: str
    meals: Optional[dict] = None


class CookSessionCreate(BaseModel):
    meal_plan_id: int
    day: str
    meal_name: str


class PlannerChatRequest(BaseModel):
    message: str


class CookChatRequest(BaseModel):
    message: str
    cook_session_id: int


# ---- Startup ----

@app.on_event("startup")
def on_startup():
    init_db()


# ---- Household Routes ----

@app.get("/household")
def get_household(session: Session = Depends(get_session)):
    members = session.exec(select(HouseholdMember)).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "dietary_restrictions": json.loads(m.dietary_restrictions),
            "allergies": json.loads(m.allergies),
            "preferences": json.loads(m.preferences)
        }
        for m in members
    ]


@app.post("/household")
def add_member(member: HouseholdMemberCreate, session: Session = Depends(get_session)):
    new_member = HouseholdMember(
        name=member.name,
        dietary_restrictions=json.dumps(member.dietary_restrictions),
        allergies=json.dumps(member.allergies),
        preferences=json.dumps(member.preferences)
    )
    session.add(new_member)
    session.commit()
    session.refresh(new_member)
    return {"id": new_member.id, "name": new_member.name}


# ---- Meal Plan Routes ----

@app.get("/meal-plans")
def list_meal_plans(session: Session = Depends(get_session)):
    plans = session.exec(select(MealPlan).order_by(MealPlan.id.desc())).all()
    return [
        {"id": p.id, "week_start": p.week_start, "status": p.status}
        for p in plans
    ]


@app.get("/meal-plans/{plan_id}")
def get_meal_plan(plan_id: int, session: Session = Depends(get_session)):
    plan = session.get(MealPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return {
        "id": plan.id,
        "week_start": plan.week_start,
        "status": plan.status,
        "meals": json.loads(plan.meals)
    }


@app.post("/meal-plans")
def create_meal_plan(data: MealPlanCreate, session: Session = Depends(get_session)):
    from tools.meal_tools import DEMO_MEAL_PLAN
    meals = data.meals or DEMO_MEAL_PLAN
    plan = MealPlan(
        week_start=data.week_start,
        status="planning",
        meals=json.dumps(meals)
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return {"id": plan.id, "week_start": plan.week_start, "status": plan.status}


@app.put("/meal-plans/{plan_id}/approve")
def approve_meal_plan(plan_id: int, session: Session = Depends(get_session)):
    plan = session.get(MealPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    plan.status = "approved"
    session.add(plan)
    session.commit()
    return {"id": plan.id, "status": plan.status, "message": "Meal plan approved!"}


# ---- Grocery List Routes ----

@app.get("/grocery-lists/{meal_plan_id}")
def get_grocery_list(meal_plan_id: int, session: Session = Depends(get_session)):
    grocery = session.exec(
        select(GroceryList).where(GroceryList.meal_plan_id == meal_plan_id)
    ).first()
    if not grocery:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    return {
        "id": grocery.id,
        "meal_plan_id": grocery.meal_plan_id,
        "items": json.loads(grocery.items),
        "status": grocery.status
    }


@app.post("/grocery-lists/{meal_plan_id}/generate")
def generate_grocery_list(meal_plan_id: int, session: Session = Depends(get_session)):
    plan = session.get(MealPlan, meal_plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    meals = json.loads(plan.meals)
    items = consolidate_grocery_list(meals)

    # Check if grocery list exists
    existing = session.exec(
        select(GroceryList).where(GroceryList.meal_plan_id == meal_plan_id)
    ).first()

    if existing:
        existing.items = json.dumps(items)
        existing.status = "pending"
        session.add(existing)
        session.commit()
        session.refresh(existing)
        grocery = existing
    else:
        grocery = GroceryList(
            meal_plan_id=meal_plan_id,
            items=json.dumps(items),
            status="pending"
        )
        session.add(grocery)
        session.commit()
        session.refresh(grocery)

    return {
        "id": grocery.id,
        "meal_plan_id": grocery.meal_plan_id,
        "items": items,
        "status": grocery.status
    }


@app.post("/grocery-lists/{meal_plan_id}/order")
def order_groceries(meal_plan_id: int, session: Session = Depends(get_session)):
    grocery = session.exec(
        select(GroceryList).where(GroceryList.meal_plan_id == meal_plan_id)
    ).first()
    if not grocery:
        raise HTTPException(status_code=404, detail="Grocery list not found")

    items = json.loads(grocery.items)
    result = simulate_instamart_order(items)

    grocery.status = "ordered"
    session.add(grocery)
    session.commit()

    return result


# ---- Cook Session Routes ----

@app.post("/cook-sessions")
def start_cook_session(data: CookSessionCreate, session: Session = Depends(get_session)):
    cook_session = CookSession(
        meal_plan_id=data.meal_plan_id,
        day=data.day,
        meal_name=data.meal_name,
        status="active"
    )
    session.add(cook_session)
    session.commit()
    session.refresh(cook_session)
    return {
        "id": cook_session.id,
        "day": cook_session.day,
        "meal_name": cook_session.meal_name,
        "status": cook_session.status
    }


@app.get("/cook-sessions/{session_id}")
def get_cook_session(session_id: int, session: Session = Depends(get_session)):
    cook_session = session.get(CookSession, session_id)
    if not cook_session:
        raise HTTPException(status_code=404, detail="Cook session not found")
    return {
        "id": cook_session.id,
        "meal_plan_id": cook_session.meal_plan_id,
        "day": cook_session.day,
        "meal_name": cook_session.meal_name,
        "status": cook_session.status,
        "notes": cook_session.notes,
        "substitutions": json.loads(cook_session.substitutions)
    }


# ---- Chat Routes ----

@app.post("/chat/planner")
def chat_planner(request: PlannerChatRequest, session: Session = Depends(get_session)):
    from agents.planner import PlannerAgent
    agent = PlannerAgent(db_session=session)
    response = agent.chat(request.message)
    return {"response": response}


@app.post("/chat/cook")
def chat_cook(request: CookChatRequest, session: Session = Depends(get_session)):
    from agents.cook import CookAgent
    agent = CookAgent(db_session=session)
    response = agent.chat(request.message, request.cook_session_id)
    return {"response": response}


# ---- Conversation History ----

@app.get("/conversations/{session_type}")
def get_conversations(session_type: str, session: Session = Depends(get_session)):
    messages = session.exec(
        select(ConversationMessage)
        .where(ConversationMessage.session_type == session_type)
        .order_by(ConversationMessage.timestamp)
    ).all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp
        }
        for m in messages
    ]


# ---- Static Files ----

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
